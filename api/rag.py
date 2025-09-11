# Elimina todos los documentos PDF y su contexto para una sesión
def delete_docs_for_session(session_id: str):
    # Eliminar archivos PDF
    for fname in os.listdir(UPLOAD_DIR):
        if fname.endswith(".pdf") and fname.startswith(f"{session_id}_"):
            try:
                os.remove(os.path.join(UPLOAD_DIR, fname))
            except Exception as e:
                print(f"Error eliminando archivo {fname}: {e}")
    # Eliminar del vector DB
    if _collection:
        _collection.delete(where={"client_id": session_id})

# Elimina un documento PDF y su contexto de una sesión
def delete_single_doc(session_id: str, filename: str):
    # Eliminar archivo PDF
    file_path = os.path.join(UPLOAD_DIR, filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error eliminando archivo {filename}: {e}")
    # Eliminar del vector DB (por metadatos)
    try:
        if _collection:
            # ChromaDB espera solo un campo en where, usamos 'source' para eliminar el documento específico
            _collection.delete(where={"source": filename})
    except Exception as e:
        print(f"Error eliminando del vector DB {filename}: {e}")
    return True

# Devuelve la lista de documentos PDF subidos para una sesión
def get_docs_for_session(session_id: str):
    docs = []
    if not os.path.exists(UPLOAD_DIR):
        return docs
    for fname in os.listdir(UPLOAD_DIR):
        if fname.endswith(".pdf") and fname.startswith(f"{session_id}_"):
            docs.append(fname)
    return docs
def list_documents_by_client(client_id: str) -> list:
    if _collection is None:
        return []
    results = _collection.get(where={"client_id": client_id})
    docs = set()
    for meta in results.get("metadatas", []):
        if meta and "original_filename" in meta:
            docs.add(meta["original_filename"])
        elif meta and "source" in meta:
            docs.add(meta["source"])
    return list(docs)
import os
import traceback
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-mpnet-base-v2")
CHROMA_DIR = os.getenv("CHROMA_DIR", "storage/vectordb")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "storage/uploads")
COLLECTION = "docs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

_client = None
_collection = None
_embedder = None

try:
    _client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(allow_reset=False))
    _collection = _client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
except Exception:
    print("Warning: fallo inicializando chromadb persistent client, usando cliente en memoria.\n", traceback.format_exc())
    try:
        _client = chromadb.Client(Settings())
        _collection = _client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    except Exception:
        print("Error: no se pudo inicializar chroma client:\n", traceback.format_exc())
        _collection = None

try:
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
        tb = traceback.format_exc()
        raise RuntimeError(f"Error generating embeddings: {e}\n{tb}")


def pdf_to_text(path: str) -> str:
    try:
        with open(path, "rb") as f:
            reader = PdfReader(f)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        print(f"Warning: fallo extrayendo texto de PDF {path}:\n", traceback.format_exc())
        return ""


def chunk(text: str, size: int = 400, overlap: int = 100) -> list[str]:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        part = words[i:i+size]
        chunks.append(" ".join(part))
        i += size - overlap
    return chunks


def add_document(file_path: str, client_id: str, original_filename: str = None) -> int:
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
    metas = [{
        "client_id": client_id,
        "source": os.path.basename(file_path),
        "original_filename": original_filename or os.path.basename(file_path),
        "chunk": i
    } for i in range(len(pieces))]
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
