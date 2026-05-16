"""
Automated feedback-driven tuning loop for QuoteSelector.
Periodically collects user feedback and updates selection logic.
To be scheduled via cron or a task runner (e.g., hourly).
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.quote_selector import QuoteSelector
from app.core.feedback_logger import collect_feedback_for_tuning
from app.core.openai_compat import openai_semantic_score
from app.core.feedback_logger import log_quote_feedback
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auto_tune_quote_selector")

# Configure your DB connection string
DATABASE_URL = settings.database_url  # Ensure this is set in your config
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def run_tuning_loop():
    logger.info("Starting QuoteSelector tuning loop...")
    db = Session()
    try:
        feedback_data = collect_feedback_for_tuning(db, days=7)
        selector = QuoteSelector(nlp_model=openai_semantic_score, feedback_logger=log_quote_feedback)
        selector.update_feedback_weights(feedback_data)
        logger.info(f"Tuning complete. Processed {len(feedback_data)} feedback entries.")
    except Exception as e:
        logger.error(f"Tuning loop failed: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    run_tuning_loop()
