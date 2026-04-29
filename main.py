import logging
import os
from telegram.ext import ApplicationBuilder
from config import Config
from storage.migrations import run_migrations
from storage.database import Database
from bot.handlers import setup_handlers
from scheduler.scheduler import ThreadScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    os.makedirs("data", exist_ok=True)

    run_migrations(Config.DB_PATH)
    db = Database(Config.DB_PATH)

    app = ApplicationBuilder().token(Config.TELEGRAM_BOT_TOKEN).build()
    app.bot_data["db"] = db

    setup_handlers(app)

    thread_scheduler = ThreadScheduler(db, bot=app.bot)
    thread_scheduler.start()
    app.bot_data["scheduler"] = thread_scheduler

    logger.info("Bot starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
