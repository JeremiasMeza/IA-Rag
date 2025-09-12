import os
import httpx
from fastapi import APIRouter, Body, Response
from main import OLLAMA_URL, DEFAULT_MODEL

router = APIRouter()

@router.get("/selected_model")
def get_selected_model():
    try:
        with open(os.path.join(os.path.dirname(__file__), "../model_selected.txt"), "r", encoding="utf-8") as f:
            model = f.read().strip()
        return {"selected_model": model}
    except Exception as e:
        return {"selected_model": DEFAULT_MODEL, "error": str(e)}

@router.post("/selected_model")
def set_selected_model(model: str = Body(..., embed=True)):
    try:
        model = model.strip()
        with open(os.path.join(os.path.dirname(__file__), "../model_selected.txt"), "w", encoding="utf-8") as f:
            f.write(model)
        # Precalentar el modelo seleccionado
        import asyncio
        import time
        async def warmup():
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    await client.post(f"{OLLAMA_URL}/api/chat", json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Hola"}]
                    })
            except Exception as e:
                print(f"[WARN] No se pudo precalentar el modelo {model}: {e}")
        # Ejecutar el warmup de forma asíncrona si estamos en un contexto async, si no, crear uno nuevo
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(warmup())
        except RuntimeError:
            asyncio.run(warmup())
        return {"ok": True, "selected_model": model}
    except Exception as e:
        return {"ok": False, "error": str(e)}


    except Exception as e:
        return {"model": None, "loaded": False, "error": str(e)}
