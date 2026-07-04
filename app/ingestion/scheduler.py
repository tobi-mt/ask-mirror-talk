import logging
from apscheduler.schedulers.blocking import BlockingScheduler

from app.core.db import SessionLocal
from app.core.config import settings
from app.core.logging import setup_logging
from app.ingestion.pipeline import run_ingestion

setup_logging()
logger = logging.getLogger(__name__)


def run_job():
    db = SessionLocal()
    try:
        result = run_ingestion(db)
        logger.info("Ingestion run complete: %s", result)
    finally:
        db.close()


def start_scheduler():
    scheduler = BlockingScheduler()
    scheduler.add_job(run_job, "interval", minutes=settings.rss_poll_minutes)
    scheduler.start()


if __name__ == "__main__":
    start_scheduler()
