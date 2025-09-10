




import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx
import rag

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("MODEL_NAME", "qwen2.5:1.5b")  # actualizado default
SYSTEM_PROMPT = (
    "Eres un asistente conversacional. Responde siempre en español, de forma breve y clara. "
    "No muestres tu razonamiento interno ni incluyas etiquetas como <think> o similares. "
    "Limítate a ofrecer la respuesta final en texto plano usando únicamente el texto proporcionado. "
    "Si la respuesta no está en el texto, responde: 'No encontrado en el texto.'"
)

app = FastAPI(title="Chat PDF + Ollama")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatIn(BaseModel):
    message: str
    model: str | None = None
    session_id: str

@app.get("/")
def root():
    return {"ok": True, "service": "Chat PDF + Ollama", "endpoints": ["/health", "/upload_pdf", "/chat", "/docs"]}

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload_pdf")
async def upload_pdf(session_id: str = Form(None), file: UploadFile = File(...)):
    session_id = session_id or "global"
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
    upload_dir = rag.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    unique_name = f"{session_id}_{uuid.uuid4().hex}.pdf"
    file_path = os.path.join(upload_dir, unique_name)
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando PDF: {e}")
    try:
        num_chunks = rag.add_document(file_path, session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando PDF: {e}")
    return {"ok": True, "session_id": session_id, "chunks": num_chunks}


from fastapi.responses import PlainTextResponse

@app.post("/chat", response_class=PlainTextResponse)
async def chat(body: ChatIn):
    session_id = getattr(body, "session_id", None) or "global"
    try:
        relevant_chunks = rag.query_relevant(body.message, session_id, top_k=4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando contexto: {e}")
    context = "\n".join([c["text"] for c in relevant_chunks]) if relevant_chunks else ""
    if not context:
        context = "No encontrado en el texto."
    prompt = (
        "Usa exclusivamente la siguiente información extraída de un PDF para responder. "
        "Si la respuesta no está en el texto, responde: 'No encontrado en el texto.'\n\n"
        f"Texto proporcionado:\n{context}\n\nPregunta: {body.message}"
    )
    payload = {
        "model": body.model or DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "raw": True
    }
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error hablando con Ollama: {e}")
    content = (data.get("message") or {}).get("content", "")
    if not content:
        raise HTTPException(status_code=500, detail="Respuesta vacía del modelo")
    import re
    content = re.sub(r'<think>[\s\S]*?</think>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'<[^>]+>', '', content)
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if lines:
        content = lines[-1]
    content = content.strip().replace('\\n', '\n').replace('\\"', '"').replace('\\', '')
    content = content.strip('"').strip("'")
    try:
        import json
        parsed = json.loads(content)
        if isinstance(parsed, dict) and 'respuesta' in parsed:
            content = parsed['respuesta']
        elif isinstance(parsed, str):
            content = parsed
    except Exception:
        pass
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    respuesta = None
    for line in lines:
        if (
            len(line) <= 200 and
            not re.search(r'(razonamiento|instrucci[oó]n|think|user sent|they want|respuesta es|so the correct answer|let me check|the answer should|simple response|extra text|confirm|testing|spanish|should be|no encontrado en el texto|okay|spanish for|just the word|without any explanation|the user might|i should reply|starting a conversation|make sure not to add anything else)', line, re.IGNORECASE)
            and not line.startswith('"') and not line.endswith('"')
            and not line.startswith("'") and not line.endswith("'")
        ):
            respuesta = line
            break
    if not respuesta:
        for line in lines:
            if 'no encontrado en el texto' in line.lower():
                respuesta = 'No encontrado en el texto.'
                break
    if not respuesta and lines:
        respuesta = min(lines, key=len).strip('"').strip("'")
    if not respuesta:
        respuesta = 'No encontrado en el texto.'
    return respuesta.strip()
