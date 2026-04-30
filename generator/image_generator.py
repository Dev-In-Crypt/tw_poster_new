import httpx
import tempfile
import os
import base64
import asyncio
from abc import ABC, abstractmethod
from config import Config


class BaseImageProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Returns path to downloaded image file."""
        ...


class DalleProvider(BaseImageProvider):
    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "dall-e-3",
                    "prompt": prompt,
                    "n": 1,
                    "size": "1792x1024",
                    "quality": "standard",
                },
            )
            resp.raise_for_status()
            image_url = resp.json()["data"][0]["url"]
            return await self._download(client, image_url)

    async def _download(self, client: httpx.AsyncClient, url: str) -> str:
        resp = await client.get(url)
        fd, path = tempfile.mkstemp(suffix=".png")
        with os.fdopen(fd, "wb") as f:
            f.write(resp.content)
        return path


class OpenRouterImageProvider(BaseImageProvider):
    """Image generation via OpenRouter (e.g. google/gemini-2.5-flash-image)."""

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": Config.IMAGE_MODEL,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                },
            )
            resp.raise_for_status()

        message = resp.json()["choices"][0]["message"]

        # OpenRouter Gemini puts images in message.images (not message.content)
        for source in [
            message.get("images") or [],
            message.get("content") if isinstance(message.get("content"), list) else [],
        ]:
            for part in source:
                if isinstance(part, dict) and part.get("type") == "image_url":
                    url = part["image_url"]["url"]
                    if url.startswith("data:"):
                        return self._save_base64(url)
                    async with httpx.AsyncClient(timeout=60) as c:
                        return await self._download(c, url)

        # Fallback: plain data URL in content
        content = message.get("content")
        if isinstance(content, str) and content.startswith("data:"):
            return self._save_base64(content)

        raise RuntimeError(f"No image found in OpenRouter response: {message!r}")

    def _save_base64(self, data_url: str) -> str:
        header, b64data = data_url.split(",", 1)
        ext = "png" if "png" in header else "jpg"
        fd, path = tempfile.mkstemp(suffix=f".{ext}")
        with os.fdopen(fd, "wb") as f:
            f.write(base64.b64decode(b64data))
        return path

    async def _download(self, client: httpx.AsyncClient, url: str) -> str:
        resp = await client.get(url)
        fd, path = tempfile.mkstemp(suffix=".png")
        with os.fdopen(fd, "wb") as f:
            f.write(resp.content)
        return path


class ReplicateProvider(BaseImageProvider):
    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Bearer {Config.REPLICATE_API_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={
                    "version": "latest",
                    "input": {
                        "prompt": prompt,
                        "width": 1792,
                        "height": 1024,
                    },
                },
            )
            resp.raise_for_status()
            prediction = resp.json()

            while prediction["status"] not in ("succeeded", "failed"):
                await asyncio.sleep(2)
                resp = await client.get(
                    prediction["urls"]["get"],
                    headers={"Authorization": f"Bearer {Config.REPLICATE_API_TOKEN}"},
                )
                prediction = resp.json()

            if prediction["status"] == "failed":
                raise RuntimeError("Image generation failed")

            image_url = prediction["output"][0]
            async with httpx.AsyncClient(timeout=60) as client:
                return await DalleProvider()._download(client, image_url)


def get_image_provider() -> BaseImageProvider:
    providers = {
        "openai": DalleProvider,
        "dalle": DalleProvider,
        "replicate": ReplicateProvider,
        "openrouter": OpenRouterImageProvider,
        "gemini": OpenRouterImageProvider,
    }
    provider_cls = providers.get(Config.IMAGE_PROVIDER, DalleProvider)
    return provider_cls()
