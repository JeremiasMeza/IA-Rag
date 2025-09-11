## Prompt estructurado (nuevo)

El endpoint `/chat` ahora utiliza un prompt de sistema estructurado que instruye al modelo a devolver SIEMPRE un JSON con la siguiente forma:

```
{
   "answer": "<texto con markdown básico y citas [src:ID|p]>",
   "follow_up": ["pregunta_corta_1", "pregunta_corta_2"],
   "used_sources": [{"id":"ctx-00","source":"archivo.pdf","page":1}],
   "confidence": "LOW|MEDIUM|HIGH"
}
```

Parámetros opcionales que puede enviar el cliente en el body POST:

| Campo | Descripción | Valores / Ejemplo | Default |
|-------|-------------|-------------------|---------|
| answer_mode | Estilo de salida | `breve` | `breve` |
| locale | Localización idioma | `es-AR` | `es-AR` |
| max_tokens | Límite lógico de generación | `400` | 400 |
| score_threshold | Umbral mínimo de score (filtro lógico) | `0.0` | 0.0 |

Los `context_chunks` se construyen internamente y se pasan como JSON al modelo: cada chunk incluye `id`, `source`, `page`, `text`, `score`.

Si el modelo no produce un JSON válido, el servidor hace un fallback generando un JSON mínimo con `answer` y `confidence` = LOW.

Local RAG API (Ollama + Chroma)

Quick start

1. Create a virtualenv and install dependencies:

   C:/path/to/python -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; pip install -r requirements.txt

2. Copy `.env.example` to `.env` and adjust variables (OLLAMA_URL, ADMIN_TOKEN...)
   Default chat model ahora: `qwen2.5:1.5b` (puedes cambiarlo con MODEL_NAME en `.env`).

3. Run the API with uvicorn:

   .\.venv\Scripts\uvicorn.exe main:app --reload --host 0.0.0.0 --port 8000

4. Frontend expects VITE_API_URL pointing to the backend (default http://127.0.0.1:8000)

5. El historial de chat se guarda en memoria por `client_id` y puede limpiarse sin
   afectar los documentos indexados:

   `curl -X DELETE "http://localhost:8000/chat/context?client_id=CLIENTE"`
