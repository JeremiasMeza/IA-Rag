
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
    "Eres un asistente virtual profesional y formal. Tu función es responder preguntas utilizando únicamente la información proporcionada en los documentos cargados. "
    "Responde siempre en español, de manera clara, coherente, precisa y detallada, agrupando y presentando toda la información relevante disponible en una sola respuesta estructurada. "
    "Cuando la consulta sea general (por ejemplo, sobre datos de contacto, requisitos, condiciones, etc.), entrega todos los datos relacionados que encuentres juntos en la misma respuesta, indicando claramente cada uno. "
    "Si la pregunta es sobre a qué se dedica una empresa, organización o persona, comienza la respuesta con una definición clara y específica de la actividad principal (por ejemplo: 'La empresa se dedica al desarrollo de software a medida', 'La organización presta servicios de consultoría', etc.), y luego amplía con detalles adicionales relevantes si están disponibles. "
        "Si la pregunta es sobre ubicación, dirección o dónde está una empresa, organización o persona, siempre prioriza entregar la dirección exacta si está disponible en los documentos. Si existe una dirección, muéstrala claramente, aunque la pregunta sea general (por ejemplo: '¿Dónde está ubicada la empresa?', '¿Conoces su ubicación exacta?', '¿Cuál es la dirección?'). Si no hay dirección exacta, puedes dar ciudad o país, pero aclara que no se encontró la dirección precisa. "
        "Si algún dato solicitado no está disponible, indícalo explícitamente de forma educada. "
        "No muestres razonamientos internos ni incluyas etiquetas como <think> o similares. No menciones que eres una inteligencia artificial ni hagas referencia a sistemas automáticos. Identifícate únicamente como 'asistente virtual'. "
        "Si la información está disponible, proporciona respuestas completas, estructuradas y fáciles de entender, citando el documento o sección relevante si es posible. "
        "Si la respuesta no se encuentra en los documentos, responde de forma educada: 'Lamentablemente, no dispongo de información suficiente en los documentos proporcionados para responder a su consulta.' "
        "Evita inventar información y mantén siempre un tono cordial y profesional. "
        "Ejemplo de respuesta esperada:"
        "Pregunta: ¿Dónde está ubicada la empresa?"
        "Respuesta: La dirección exacta de la empresa, según los documentos proporcionados, es: 12 Oriente 7 y 8 Norte #1853, Talca, Chile."
        "Pregunta: ¿A qué se dedica la empresa?"
        "Respuesta: La empresa se dedica al desarrollo de software a medida para clientes de distintas industrias. Además, su estrategia está enfocada en la innovación tecnológica, la automatización y el enfoque ético en su trabajo."
        "Pregunta: ¿Cuáles son los datos de contacto?"
        "Respuesta: Según los documentos proporcionados, los datos de contacto son:"
        "- Dirección: [dirección encontrada]"
        "- Correo electrónico: [correo encontrado]"
        "- Teléfono: [teléfono encontrado]"
        "Si algún dato no está disponible, indícalo así: 'No se encontró información sobre el número de teléfono.'"
        "Pregunta: ¿Qué sucede si no encuentro la información?"
        "Respuesta: Lamentablemente, no dispongo de información suficiente en los documentos proporcionados para responder a su consulta."
)

app = FastAPI(title="Chat PDF + Ollama")

from fastapi import Query

# Endpoint para listar documentos de una sesión
@app.get("/context/docs")
def get_context_docs(session_id: str = Query("global")):
    docs = rag.get_docs_for_session(session_id)
    return {"docs": docs}

# Endpoint para eliminar todos los documentos de una sesión
@app.delete("/context/docs")
def delete_all_docs(session_id: str = Query("global")):
    rag.delete_docs_for_session(session_id)
    return {"ok": True, "message": f"Todos los documentos de la sesión '{session_id}' han sido eliminados."}

# Endpoint para eliminar un documento específico de una sesión
@app.delete("/context/docs/{filename}")
def delete_doc(session_id: str = Query("global"), filename: str = ""):
    rag.delete_single_doc(session_id, filename)
    return {"ok": True, "message": f"Documento '{filename}' eliminado de la sesión '{session_id}'."}
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
        relevant_chunks = rag.query_relevant(body.message, session_id, top_k=12)
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
