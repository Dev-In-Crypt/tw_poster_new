import random
import logging
import os
import httpx
from generator.thread_generator import ThreadGenerator
from generator.image_generator import get_image_provider
from publisher.twitter_client import TwitterPublisher
from storage.database import Database
from config import Config

logger = logging.getLogger(__name__)

STYLES = ["educational", "hot_take", "news_breakdown"]


async def run_pipeline(
    db: Database,
    topic: str | None = None,
    style: str | None = None,
    num_tweets: int = 7,
) -> dict:
    """Full pipeline: topic → generate → image → post → save."""
    generator = ThreadGenerator()
    image_provider = get_image_provider()
    publisher = TwitterPublisher()

    if topic is None:
        topic = await _pick_auto_topic(generator, db)

    if style is None:
        style = random.choice(STYLES)

    recent_topics = db.get_recent_topics(30)

    logger.info(f"Generating thread: topic='{topic}', style='{style}'")

    tweets = await generator.generate_thread(
        topic=topic, style=style, num_tweets=num_tweets,
        recent_topics=recent_topics,
    )

    image_path = None
    try:
        img_prompt = await generator.generate_image_prompt(topic)
        image_path = await image_provider.generate(img_prompt)
        logger.info(f"Image generated: {image_path}")
    except Exception as e:
        logger.warning(f"Image generation failed, posting without: {e}")

    thread_id = db.save_thread(topic, style, tweets, image_path)

    try:
        twitter_id = publisher.post_thread(tweets, image_path)
        db.mark_posted(thread_id, twitter_id)
        logger.info(f"Thread posted: twitter_id={twitter_id}")
    except Exception as e:
        logger.error(f"Twitter posting failed: {e}")
        return {
            "status": "error",
            "thread_id": thread_id,
            "error": str(e),
            "tweets": tweets,
        }
    finally:
        if image_path and os.path.exists(image_path):
            os.unlink(image_path)

    db.save_topic(topic)

    return {
        "status": "posted",
        "thread_id": thread_id,
        "twitter_id": twitter_id,
        "topic": topic,
        "style": style,
        "num_tweets": len(tweets),
        "tweets": tweets,
    }


async def _pick_auto_topic(generator: ThreadGenerator, db: Database) -> str:
    recent = db.get_recent_topics(30)

    prompt = f"""Suggest ONE specific trending topic for a Twitter thread about Crypto/Web3 or Tech/AI.
Topic should be timely, specific, and engaging.

AVOID these recent topics:
{chr(10).join(f'- {t}' for t in recent) if recent else 'None yet'}

Return ONLY the topic as a short phrase (5-10 words), nothing else."""

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": Config.OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.9,
                "max_tokens": 100,
            },
        )
        resp.raise_for_status()

    return resp.json()["choices"][0]["message"]["content"].strip().strip('"')
