import asyncio
import sys
import shutil
sys.path.insert(0, "/app")

from generator.thread_generator import ThreadGenerator
from generator.image_generator import get_image_provider

TOPICS = [
    "Why Bitcoin ETFs changed crypto forever",
    "How AI agents are replacing human jobs in 2025",
]

async def main():
    gen = ThreadGenerator()
    provider = get_image_provider()
    print(f"Image provider: {type(provider).__name__}\n")

    for i, topic in enumerate(TOPICS, 1):
        print(f"[{i}/{len(TOPICS)}] Topic: {topic}")
        img_prompt = await gen.generate_image_prompt(topic)
        print(f"  Image prompt: {img_prompt}")

        try:
            path = await provider.generate(img_prompt)
            dest = f"/app/data/test_image_{i}.png"
            shutil.copy(path, dest)
            import os; os.unlink(path)
            print(f"  ✅ Saved: {dest}\n")
        except Exception as e:
            print(f"  ❌ Failed: {e}\n")

asyncio.run(main())
