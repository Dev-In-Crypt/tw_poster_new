import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from storage.database import Database
from pipeline import run_pipeline
from config import Config

logger = logging.getLogger(__name__)


class ThreadScheduler:
    def __init__(self, db: Database, bot=None):
        self.db = db
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=Config.TIMEZONE)

    def start(self):
        schedules = self.db.get_schedules()
        for s in schedules:
            self._add_job(s["id"], s["hour"], s["minute"])

        if not schedules:
            self._add_job(
                "default",
                Config.DEFAULT_POST_HOUR,
                Config.DEFAULT_POST_MINUTE,
            )

        self.scheduler.start()
        logger.info(f"Scheduler started with {len(schedules)} jobs")

    def _add_job(self, job_id, hour: int, minute: int):
        self.scheduler.add_job(
            self._scheduled_post,
            trigger=CronTrigger(hour=hour, minute=minute),
            id=f"thread_{job_id}",
            replace_existing=True,
        )
        logger.info(f"Scheduled job: {hour:02d}:{minute:02d} UTC")

    async def _scheduled_post(self):
        logger.info("Running scheduled thread post...")
        try:
            result = await run_pipeline(self.db)

            if self.bot:
                status = "✅" if result["status"] == "posted" else "❌"
                msg = (
                    f"{status} Scheduled thread\n"
                    f"Topic: {result.get('topic', 'N/A')}\n"
                    f"Status: {result['status']}"
                )
                await self.bot.send_message(
                    chat_id=Config.TELEGRAM_ADMIN_ID, text=msg
                )
        except Exception as e:
            logger.error(f"Scheduled post failed: {e}")
            if self.bot:
                await self.bot.send_message(
                    chat_id=Config.TELEGRAM_ADMIN_ID,
                    text=f"❌ Scheduled post failed:\n{e}",
                )

    def add_schedule(self, hour: int, minute: int):
        self.db.add_schedule(hour, minute)
        schedules = self.db.get_schedules()
        job_id = schedules[-1]["id"]
        self._add_job(job_id, hour, minute)

    def stop(self):
        self.scheduler.shutdown()
