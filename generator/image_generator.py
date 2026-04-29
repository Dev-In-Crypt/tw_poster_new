import httpx
import tempfile
import os
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
                    headers={
                        "Authorization": f"Bearer {Config.REPLICATE_API_TOKEN}",
                    },
                )
                prediction = resp.json()

            if prediction["status"] == "failed":
                raise RuntimeError("Image generation failed")

            image_url = prediction["output"][0]
            return await DalleProvider()._download(client, image_url)


def get_image_provider() -> BaseImageProvider:
    providers = {
        "openai": DalleProvider,
        "dalle": DalleProvider,
        "replicate": ReplicateProvider,
    }
    provider_cls = providers.get(Config.IMAGE_PROVIDER, DalleProvider)
    return provider_cls()
