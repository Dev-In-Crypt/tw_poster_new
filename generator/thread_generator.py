import json
import random
import httpx
from config import Config
from generator.prompts import (
    SYSTEM_PROMPT,
    IMAGE_PROMPT_SYSTEM,
    STYLE_INSTRUCTIONS,
    build_thread_prompt,
)


class ThreadGenerator:
    def __init__(self):
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        self.model = Config.OPENROUTER_MODEL

    async def generate_thread(
        self, topic: str, style: str | None = None, num_tweets: int = 7,
        recent_topics: list[str] | None = None,
    ) -> list[str]:
        if style is None:
            style = random.choice(list(STYLE_INSTRUCTIONS.keys()))

        prompt = build_thread_prompt(
            topic, style, num_tweets, recent_topics or []
        )

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.8,
                    "max_tokens": 3000,
                },
            )
            resp.raise_for_status()

        content = resp.json()["choices"][0]["message"]["content"]
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]

        tweets = json.loads(content)
        validated = []
        for t in tweets:
            if len(t) > 280:
                t = t[:277] + "..."
            validated.append(t)

        return validated

    async def generate_image_prompt(self, topic: str) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": IMAGE_PROMPT_SYSTEM},
                        {"role": "user", "content": f"Topic: {topic}"},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 300,
                },
            )
            resp.raise_for_status()

        return resp.json()["choices"][0]["message"]["content"].strip()
