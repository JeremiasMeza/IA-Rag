
import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx
from pypdf import PdfReader

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("MODEL_NAME", "llama3.1:8b")

app = FastAPI(title="Chat PDF + Ollama")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Guardar textos PDF en memoria por sesión
PDF_CONTEXTS = {}

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
async def upload_pdf(session_id: str = Form(...), file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
    import io
    text = ""
    try:
        file_bytes = await file.read()
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo PDF: {e}")
    PDF_CONTEXTS[session_id] = text
    return {"ok": True, "session_id": session_id, "chars": len(text)}

@app.post("/chat")
async def chat(body: ChatIn):
    context = PDF_CONTEXTS.get(body.session_id, "")
    if not context:
        raise HTTPException(status_code=400, detail="No hay PDF cargado para esta sesión")
    prompt = (
        "Responde solo con el dato solicitado usando únicamente la siguiente información extraída de un PDF. "
        "No repitas la pregunta, no des contexto, explicaciones ni razonamientos. "
        "Si la respuesta no está en el texto, responde: 'No encontrado en el texto'.\n\n"
        f"Texto extraído:\n{context}\n\nPregunta: {body.message}"
    )
    payload = {
        "model": body.model or DEFAULT_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error hablando con Ollama: {e}")
    content = (data.get("message") or {}).get("content")
    if not content:
        raise HTTPException(status_code=500, detail="Respuesta vacía del modelo")
    return content
