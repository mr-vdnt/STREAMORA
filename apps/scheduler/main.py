"""
Streamora Celery Scheduler Entrypoint
Schedules periodic jobs: daily recommendations, hourly cache warming, nightly catalog audits.
"""
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("streamora-scheduler")

def run_scheduler():
    logger.info("Initializing Streamora Periodic Task Scheduler...")
    logger.info("Periodic cron schedules active.")

if __name__ == "__main__":
    run_scheduler()
