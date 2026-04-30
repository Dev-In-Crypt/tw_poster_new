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
            if len(t) > 250:
                t = await self._shorten_tweet(t)
            validated.append(t)

        return validated

    async def _shorten_tweet(self, tweet: str) -> str:
        """Ask the model to shorten a tweet to under 250 chars while preserving meaning."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                f"Shorten this tweet to under 250 characters (including spaces and punctuation) "
                                f"while preserving its meaning. Return ONLY the shortened tweet text, nothing else.\n\n"
                                f"Tweet: {tweet}"
                            ),
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 200,
                },
            )
            resp.raise_for_status()
        result = resp.json()["choices"][0]["message"]["content"].strip()
        # Hard fallback if model still returns too long
        if len(result) > 250:
            result = result[:247].rsplit(" ", 1)[0] + "..."
        return result

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
