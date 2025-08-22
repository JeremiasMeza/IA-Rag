Local RAG API (Ollama + Chroma)

Quick start

1. Create a virtualenv and install dependencies:

   C:/path/to/python -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; pip install -r requirements.txt

2. Copy `.env.example` to `.env` and adjust variables (OLLAMA_URL, ADMIN_TOKEN...)

3. Run the API with uvicorn:

   .\.venv\Scripts\uvicorn.exe main:app --reload --host 0.0.0.0 --port 8000

4. Frontend expects VITE_API_URL pointing to the backend (default http://127.0.0.1:8000)
