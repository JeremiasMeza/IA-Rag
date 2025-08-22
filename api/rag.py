import os
import traceback
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHROMA_DIR = os.getenv("CHROMA_DIR", "storage/vectordb")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "storage/uploads")
COLLECTION = "docs"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

# Inicialización defensiva de Chroma y el modelo de embeddings.
_client = None
_collection = None
_embedder = None

try:
    # Intentamos usar el cliente persistente; si falla, caemos a cliente en memoria
    _client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(allow_reset=False))
    _collection = _client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
except Exception:
    # No queremos que la importación del módulo rompa la app; registramos el traceback y seguimos
    print("Warning: fallo inicializando chromadb persistent client, usando cliente en memoria.\n", traceback.format_exc())
    try:
        _client = chromadb.Client(Settings())
        _collection = _client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    except Exception:
        # Como último recurso, dejamos _collection en None y fallaremos con error claro al intentar usarlo
        print("Error: no se pudo inicializar chroma client:\n", traceback.format_exc())
        _collection = None

try:
    # Forzamos carga en CPU para evitar problemas con drivers CUDA en entornos locales
    _embedder = SentenceTransformer(EMBED_MODEL, device="cpu")
except Exception:
    print("Warning: fallo cargando modelo de embeddings:\n", traceback.format_exc())
    _embedder = None


def _embed(texts: list[str]) -> list[list[float]]:
    """Genera embeddings usando SentenceTransformer cargado; lanza excepción clara si no está disponible."""
    if _embedder is None:
        raise RuntimeError("Embedding model not loaded. Check server logs for errors when loading SentenceTransformer.")
    try:
        return _embedder.encode(texts, normalize_embeddings=True).tolist()
    except Exception as e:
        # Añadimos trazas para depuración
        tb = traceback.format_exc()
        raise RuntimeError(f"Error generating embeddings: {e}\n{tb}")


def pdf_to_text(path: str) -> str:
    try:
        with open(path, "rb") as f:
            reader = PdfReader(f)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        # Devolvemos cadena vacía si no se puede extraer texto, y registramos la traza
        print(f"Warning: fallo extrayendo texto de PDF {path}:\n", traceback.format_exc())
        return ""


def chunk(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        part = words[i:i+size]
        chunks.append(" ".join(part))
        i += size - overlap
    return chunks


def add_document(file_path: str, client_id: str) -> int:
    # Leer el contenido
    if file_path.lower().endswith(".pdf"):
        text = pdf_to_text(file_path)
    else:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        except Exception:
            print(f"Warning: fallo leyendo archivo de texto {file_path}:\n", traceback.format_exc())
            text = ""

    pieces = chunk(text)
    if not pieces:
        return 0

    if _collection is None:
        raise RuntimeError("Chroma collection not initialized. Check server logs for initialization errors.")

    ids = [f"{client_id}_{os.path.basename(file_path)}_{i}" for i in range(len(pieces))]
    metas = [{"client_id": client_id, "source": os.path.basename(file_path), "chunk": i} for i in range(len(pieces))]
    # Generar embeddings y añadir a la colección
    embs = _embed(pieces)
    try:
        _collection.add(documents=pieces, embeddings=embs, metadatas=metas, ids=ids)
    except Exception as e:
        print("Error añadiendo documentos a chroma:\n", traceback.format_exc())
        raise
    return len(pieces)


def query_relevant(question: str, client_id: str, top_k: int = 4) -> list[dict]:
    res = _collection.query(
        query_embeddings=_embed([question]),
        n_results=top_k,
        where={"client_id": client_id},
    )
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    out = []
    for d, m in zip(docs, metas):
        out.append({"text": d, "meta": m})
    return out


def delete_by_client(client_id: str) -> None:
    _collection.delete(where={"client_id": client_id})


def delete_all() -> None:
    _client.delete_collection(COLLECTION)
    _client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
