


import os
import uuid
import shutil
import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import rag
from fastapi.staticfiles import StaticFiles

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("MODEL_NAME", "qwen2.5:1.5b")  # actualizado default

app = FastAPI(title="Chat PDF + Ollama")

# Precalentar modelo seleccionado al iniciar el backend (en background)
import asyncio

# --- Keep Alive del modelo ---
MODEL_KEEPALIVE_ENABLED = os.getenv("MODEL_KEEPALIVE_ENABLED", "true").lower() in ("1", "true", "yes")
MODEL_KEEPALIVE_INTERVAL = int(os.getenv("MODEL_KEEPALIVE_INTERVAL", "300"))  # segundos (default 5 min)

async def _ping_model(model: str):
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(f"{OLLAMA_URL}/api/chat", json={
                "model": model,
                "messages": [{"role": "user", "content": "ping"}]
            })
    except Exception as e:
        print(f"[KEEPALIVE] Falló ping a {model}: {e}")

async def _keepalive_loop():
    # Lee siempre el modelo actual (por si cambió)
    while True:
        try:
            model_path = os.path.join(os.path.dirname(__file__), "model_selected.txt")
            if os.path.exists(model_path):
                with open(model_path, "r", encoding="utf-8") as f:
                    model = f.read().strip()
            else:
                model = DEFAULT_MODEL
            await _ping_model(model)
        except Exception as e:
            print(f"[KEEPALIVE] Error general: {e}")
        await asyncio.sleep(MODEL_KEEPALIVE_INTERVAL)

def warmup_selected_model_background():
    async def warmup():
        try:
            model_path = os.path.join(os.path.dirname(__file__), "model_selected.txt")
            if os.path.exists(model_path):
                with open(model_path, "r", encoding="utf-8") as f:
                    model = f.read().strip()
            else:
                model = DEFAULT_MODEL
            async with httpx.AsyncClient(timeout=60) as client:
                await client.post(f"{OLLAMA_URL}/api/chat", json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Hola"}]
                })
        except Exception as e:
            print(f"[WARN] No se pudo precalentar el modelo {model}: {e}")
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(warmup())
    except RuntimeError:
        # Si no hay loop, ignora (esto solo ocurre en contextos muy raros)
        pass

@app.on_event("startup")
def on_startup():
    warmup_selected_model_background()
    if MODEL_KEEPALIVE_ENABLED:
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(_keepalive_loop())
            print(f"[KEEPALIVE] Activado cada {MODEL_KEEPALIVE_INTERVAL}s")
        except RuntimeError:
            print("[KEEPALIVE] No se pudo iniciar la tarea background")


# Registrar routers
from routers import model as model_router
app.include_router(model_router.router)

# Endpoint para obtener el modelo seleccionado globalmente
@app.get("/selected_model")
def get_selected_model():
    try:
        with open(os.path.join(os.path.dirname(__file__), "model_selected.txt"), "r", encoding="utf-8") as f:
            model = f.read().strip()
        return {"selected_model": model}
    except Exception as e:
        return {"selected_model": DEFAULT_MODEL, "error": str(e)}

# Endpoint para actualizar el modelo seleccionado globalmente
@app.post("/selected_model")
def set_selected_model(model: str = Body(..., embed=True)):
    try:
        with open(os.path.join(os.path.dirname(__file__), "model_selected.txt"), "w", encoding="utf-8") as f:
            f.write(model.strip())
        return {"ok": True, "selected_model": model.strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# Endpoint para listar modelos descargados en Ollama
@app.get("/models")
async def list_available_models():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            r.raise_for_status()
            data = r.json()
        # Extraer solo el nombre del modelo descargado
        models = [m["name"] for m in data.get("models", [])]
        return {"models": models}
    except Exception as e:
        return Response(content=f"Error consultando modelos: {e}", status_code=500)



# Prompt configurable desde .env o variable de entorno, o valor por defecto editable aquí

CUSTOM_SYSTEM_PROMPT = os.getenv(
    "CUSTOM_SYSTEM_PROMPT",
    "Eres un asistente conversacional, amable y cortés. Si la pregunta del usuario se relaciona con los documentos o el contexto proporcionado, utilízalo para dar la mejor respuesta posible en español. Si la pregunta es de saludo, cortesía o conversación general, responde de manera natural y humana, sin forzar información de los documentos. Si no hay suficiente información para una pregunta específica, dilo claramente. Responde siempre de forma clara, directa y amigable. IMPORTANTE: Entrega únicamente la respuesta final al usuario, sin explicaciones, sin etiquetas de procesamiento, sin texto adicional, sin comentarios ni pasos intermedios. No incluyas nada fuera de la respuesta solicitada. PROHIBIDO: No incluyas ningún texto de razonamiento, explicación, ni etiquetas como <think>, <explain>, <debug> o similares. Solo responde con el texto final solicitado, sin nada adicional."
)


# Servir archivos PDF subidos como estáticos
UPLOAD_DIR = os.path.abspath(rag.UPLOAD_DIR)
app.mount("/storage/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Servir archivos PDF subidos como estáticos
UPLOAD_DIR = os.path.abspath(rag.UPLOAD_DIR)
app.mount("/storage/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

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
    try:
        rag.delete_single_doc(session_id, filename)
        return {"ok": True, "message": f"Documento '{filename}' eliminado de la sesión '{session_id}'."}
    except Exception as e:
        # Siempre devolver éxito para evitar error en frontend, pero loguear el error
        print(f"Error eliminando documento: {e}")
        return {"ok": True, "message": f"Documento '{filename}' eliminado de la sesión '{session_id}' (con advertencia)."}
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
    answer_mode: str | None = None
    locale: str | None = None
    max_tokens: int | None = None
    score_threshold: float | None = None

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
    # Guardar con el nombre original, anteponiendo el session_id y evitando colisiones
    orig_name = os.path.basename(file.filename)
    base_name, ext = os.path.splitext(orig_name)
    safe_name = f"{session_id}_{base_name}{ext}"
    file_path = os.path.join(upload_dir, safe_name)
    counter = 1
    while os.path.exists(file_path):
        safe_name = f"{session_id}_{base_name}_{counter}{ext}"
        file_path = os.path.join(upload_dir, safe_name)
        counter += 1
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando PDF: {e}")
    try:
        num_chunks = rag.add_document(file_path, session_id, original_filename=orig_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando PDF: {e}")
    return {"ok": True, "session_id": session_id, "chunks": num_chunks, "filename": os.path.basename(file_path), "original_filename": orig_name}


from fastapi.responses import PlainTextResponse

import re
from typing import List

ACK_PATTERNS: List[str] = [
    r"^(si|sí|ok|vale|dale|claro|perfecto|entendido|entiendo|listo|ya)$",
    r"^(gracias|gracias\s+!*|muchas\s+gracias)!*$",
]

def is_ack(text: str) -> bool:
    t = text.strip().lower()
    for pat in ACK_PATTERNS:
        if re.match(pat, t):
            return True
    return False

def strip_markdown(text: str) -> str:
    # Quitar encabezados
    text = re.sub(r"^#+\\s+", "", text, flags=re.MULTILINE)
    # Quitar negritas / itálicas
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)
    # Quitar listas iniciales
    text = re.sub(r"^[\-*+]\\s+", "", text, flags=re.MULTILINE)
    # Quitar bloques de código/backticks
    text = text.replace("```", "").replace("`", "")
    # Quitar separadores ---
    text = re.sub(r"^---+$", "", text, flags=re.MULTILINE)
    # Compactar espacios múltiples
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

@app.post("/chat", response_class=PlainTextResponse)
async def chat(body: ChatIn):
    session_id = getattr(body, "session_id", None) or "global"
    # Detectar saludos o preguntas de cortesía simples
    cortesias = [
        r"^hola[!.¡\s,;:]*$",
        r"^buen[oa]s? (d[ií]as|tardes|noches)[!.¡\s,;:]*$",
        r"^¿?c[oó]mo est[aá]s?\??$",
        r"^¿?qu[eé] tal\??$",
        r"^hey[!.¡\s,;:]*$",
        r"^saludos[!.¡\s,;:]*$",
        r"^qué haces\??$",
        r"^cómo te va\??$",
        r"^est[aá]s ah[ií]\??$",
        r"^est[aá]s bien\??$",
        r"^todo bien\??$",
        r"^cómo va todo\??$",
        r"^cómo puedo ayudarte\??$",
        r"^ayuda[!.¡\s,;:]*$",
    ]
    texto = (body.message or "").strip().lower()
    if any(re.match(pat, texto) for pat in cortesias):
        # Respuesta interactiva, sin markdown ni mención a IA
        respuestas = [
            "¡Hola! Estoy muy bien, gracias por preguntar. ¿En qué puedo ayudarte hoy?",
            "¡Hola! ¿Sobre qué tema te gustaría conversar o necesitas ayuda?",
            "¡Hola! ¿En qué puedo ayudarte? Si tienes alguna consulta, dime sin problema.",
        ]
        import random
        return random.choice(respuestas)
    # Mensajes cortos de confirmación / continuación
    if is_ack(texto):
        return (
            "Perfecto. Dime qué te interesa: historia de la empresa, servicios, clientes, certificaciones, contacto u otro tema."
        )

    # ...existing code para contexto documental...
    try:
        relevant_chunks = rag.query_relevant(body.message, session_id, top_k=12)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando contexto: {e}")
    context_chunks = []
    for idx, c in enumerate(relevant_chunks):
        meta = c.get("meta", {})
        chunk_id = f"ctx-{idx:02d}"
        source = meta.get("original_filename") or meta.get("source") or "desconocido"
        page = meta.get("page") or meta.get("chunk") or 0
        score = meta.get("score") or 0
        context_chunks.append({
            "id": chunk_id,
            "source": source,
            "page": page,
            "text": c.get("text", ""),
            "score": score,
        })
    answer_mode = (body.answer_mode or "breve").lower()
    if answer_mode not in {"breve", "detallado", "paso-a-paso"}:
        answer_mode = "breve"
    locale = body.locale or "es-AR"
    # Construir contexto en texto plano (evitar JSON que el modelo ignore)
    def format_context(chunks: list[dict], limit_chars: int = 13000) -> str:
        parts = []
        total = 0
        for i, ch in enumerate(chunks, start=1):
            txt = ch.get("text", "").strip().replace("\n", " ")
            if not txt:
                continue
            # Truncar cada chunk solo si es muy largo
            if len(txt) > 700:
                txt = txt[:700].rsplit(" ", 1)[0] + "…"
            segment = f"[{i}] Fuente: {ch.get('source')} pág {ch.get('page')} -> {txt}"
            if total + len(segment) > limit_chars:
                break
            parts.append(segment)
            total += len(segment)
        return "\n".join(parts) if parts else "(sin fragmentos relevantes)"

    contexto_plano = format_context(context_chunks)

    system_prompt = (
        "Eres un asistente virtual conversacional en español, amable y profesional. "
        "Usa SOLO el contexto si contiene la respuesta. Si no está, di brevemente que no aparece en los documentos y sugiere pedir otro aspecto. "
        "No inventes datos. Responde en texto plano (sin markdown, sin listas con guiones, sin encabezados). "
        "No añadas prefijos como 'Respuesta final:' ni plantillas ni corchetes. Solo da la respuesta directamente."
    )

    user_message_composed = (
        f"Contexto disponible (fragmentos):\n{contexto_plano}\n\n"
        f"Pregunta: {body.message}\n"
        f"Modo: {answer_mode}. Localización: {locale}.\n"
        "Instrucciones para la respuesta: Si la respuesta está claramente en uno o varios fragmentos, intégrala en un párrafo o dos máximo. "
        "Si la información solicitada no está presente, responde: 'No encuentro esa información en los documentos disponibles.' y ofrece otra ayuda relacionada. "
        "No repitas la pregunta, no uses markdown, no agregues etiquetas internas ni explicaciones de proceso."
    )

    def build_payload(extra_system: str | None = None):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message_composed},
        ]
        if extra_system:
            messages.append({"role": "system", "content": extra_system})
        return {
            "model": body.model or DEFAULT_MODEL,
            "messages": messages,
            "stream": False
        }

    payload = build_payload()
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error hablando con Ollama: {e}")
    content = (data.get("message") or {}).get("content", "").strip()
    if not content:
        raise HTTPException(status_code=500, detail="Respuesta vacía del modelo")
    # Detectar respuesta placeholder o que replica instrucciones
    placeholder_patterns = [
        r"^respuesta final\s*:",
        r"\[aquí va la respuesta solicitada",
        r"^\s*\[?respuesta\s+final\]?",
    ]
    if any(re.search(pat, content, re.IGNORECASE) for pat in placeholder_patterns) or len(content) < 8:
        # Reintentar con recordatorio más directo
        retry_payload = build_payload("Responde ahora con el dato solicitado o indica claramente que no está en el contexto. Evita cualquier plantilla.")
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r2 = await client.post(f"{OLLAMA_URL}/api/chat", json=retry_payload)
                r2.raise_for_status()
                data2 = r2.json()
                retry_content = (data2.get("message") or {}).get("content", "").strip()
                if retry_content:
                    content = retry_content
        except Exception:
            pass
    content = strip_markdown(content)
    # Último filtro: eliminar prefijos residuales
    content = re.sub(r"^(respuesta final\s*:\s*)", "", content, flags=re.IGNORECASE).strip()
    return content
