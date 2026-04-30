import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
    TELEGRAM_ADMIN_ID = int(os.environ["TELEGRAM_ADMIN_ID"])

    # Twitter
    TWITTER_API_KEY = os.environ["TWITTER_API_KEY"]
    TWITTER_API_SECRET = os.environ["TWITTER_API_SECRET"]
    TWITTER_ACCESS_TOKEN = os.environ["TWITTER_ACCESS_TOKEN"]
    TWITTER_ACCESS_TOKEN_SECRET = os.environ["TWITTER_ACCESS_TOKEN_SECRET"]

    # OpenRouter
    OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-20250514")

    # Image
    IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "openai")
    IMAGE_MODEL = os.getenv("IMAGE_MODEL", "google/gemini-2.5-flash-image")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

    # Scheduler
    DEFAULT_POST_HOUR = int(os.getenv("DEFAULT_POST_HOUR", "10"))
    DEFAULT_POST_MINUTE = int(os.getenv("DEFAULT_POST_MINUTE", "0"))
    TIMEZONE = os.getenv("TIMEZONE", "UTC")

    # Paths
    DB_PATH = os.getenv("DB_PATH", "data/bot.db")
    TOPICS_PATH = os.getenv("TOPICS_PATH", "data/topics.json")
