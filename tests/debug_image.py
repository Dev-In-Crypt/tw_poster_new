import asyncio, sys, json, httpx, base64, os, tempfile
sys.path.insert(0, "/app")
from config import Config

async def main():
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "google/gemini-2.5-flash-image",
                "messages": [{"role": "user", "content": "Generate an image: futuristic Bitcoin logo, glowing blue neon, dark background, 16:9"}],
            },
        )
        print("Status:", resp.status_code)
        data = resp.json()
        print("Full raw response (4000 chars):")
        print(json.dumps(data, indent=2)[:4000])

asyncio.run(main())
