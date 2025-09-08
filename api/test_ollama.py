import os
import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("MODEL_NAME", "llama3.1:8b")

async def test_ollama():
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "Hola, ¿estás ahí?"}
        ],
        "stream": False
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ollama())
