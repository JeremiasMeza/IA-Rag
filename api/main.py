# api/main.py
import os
import httpx
import traceback
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# RAG helpers (asegúrate de tener rag.py con estas funciones)
from rag import add_document, query_relevant, UPLOAD_DIR

# ========= Carga de configuración (.env + variables de entorno) =========
load_dotenv()  # lee api/.env si existe

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("MODEL_NAME", "llama3.1:8b")

# RAG / control
TOP_K = int(os.getenv("TOP_K", "4"))
ANSWER_MODE = os.getenv("ANSWER_MODE", "breve")  # "breve" | "detallado" | "pasos"

# Admin
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "dev")

# ========= App =========
app = FastAPI(title="Local AI API (Ollama + RAG)")

# CORS (ajusta origins en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========= Modelos de entrada/salida =========
class ChatIn(BaseModel):
    message: str
    model: str | None = None
    client_id: str | None = None  # para aislar por cliente
    mode: str | None = None       # opcional: "breve" | "detallado" | "pasos"


# ========= Utilidades =========
def build_prompt(user_msg: str, ctx: list[dict], modo: str = "breve") -> str:
    """Plantilla de prompt con citas [n] en español y sin mostrar cadenas de pensamiento."""
    cited = "\n".join([f"[{i+1}] {c['text']}" for i, c in enumerate(ctx)])

    if modo == "breve":
        estilo = "Responde en 1–3 frases, directo al punto."
    elif modo == "pasos":
        estilo = "Responde en pasos numerados y claros."
    else:
        estilo = "Primero un resumen breve y luego detalles en viñetas."

    return (
        "Responde SIEMPRE en español. No muestres razonamientos internos, ni etiquetas "
        "<think>, ni cadenas de pensamiento. Si el contexto no es suficiente, dilo "
        "claramente y evita inventar.\n"
        f"{estilo}\n\n"
        f"Usuario: {user_msg}\n\n"
        "Contexto (si hubiera):\n"
        f"{cited if ctx else '(sin contexto)'}"
    )


# ========= Endpoints =========
@app.get("/")
def root():
    return {
        "ok": True,
        "service": "Local AI API (Ollama + RAG)",
        "endpoints": ["/health", "/chat", "/documents", "/documents (DELETE)", "/documents/all (DELETE)", "/docs"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/documents")
async def upload_document(client_id: str = Form(...), file: UploadFile = File(...)):
    """Sube un archivo (PDF o TXT), lo guarda y lo indexa en la colección del cliente."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    dest_dir = os.path.join(UPLOAD_DIR, client_id)
    os.makedirs(dest_dir, exist_ok=True)
    out_path = os.path.join(dest_dir, file.filename)

    # Guardar archivo
    with open(out_path, "wb") as f:
        f.write(await file.read())

    # Indexar
    try:
        chunks = add_document(out_path, client_id)
    except RuntimeError as e:
        # Errores previstos (modelo de embeddings o chroma no inicializado)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error indexando documento: {e}")

    return {"uploaded": file.filename, "client_id": client_id, "chunks_indexed": chunks}


@app.delete("/documents")
def delete_documents(client_id: str, x_admin_token: str = Header(None)):
    """Elimina embeddings del cliente indicado."""
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    from rag import delete_by_client 
    try:
        delete_by_client(client_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error borrando cliente: {e}")
    return {"ok": True, "deleted_client": client_id}


@app.delete("/documents/all")
def delete_everything(x_admin_token: str = Header(None)):
    """Resetea la colección completa."""
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    from rag import delete_all
    try:
        delete_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en reset total: {e}")
    return {"ok": True, "deleted": "all"}


@app.post("/chat")
async def chat(body: ChatIn):
    """Chat con Ollama. Si viene client_id, hace RAG (busca contexto) y cita [n]."""
    model = body.model or DEFAULT_MODEL

    # 1) Recuperación de contexto por cliente (opcional)
    context = []
    if body.client_id:
        try:
            context = query_relevant(body.message, body.client_id, top_k=TOP_K)
        except Exception as e:
            context = []
            print("Error buscando contexto for client_id=", body.client_id)
            print(traceback.format_exc())

    # 2) Prompt y opciones del modelo
    modo = body.mode or ANSWER_MODE
    prompt = build_prompt(body.message, context, modo=modo)

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres un asistente en español. Sé preciso, educado y evita cualquier cadena de pensamiento "
                    "u otros razonamientos internos. Si no hay evidencia suficiente en el contexto, dilo sin inventar."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,

        },
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

    return {
        "model": model,
        "used_context": len(context),
        "reply": content,
        "citations": [
            {"source": c["meta"]["source"], "chunk": c["meta"]["chunk"]} for c in context
        ],
    }
