from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal

from app.services.downsample_service import downsample_minute, downsample_hour
from app.services.retention_service import cleanup_raw_data


def start_scheduler():

    scheduler = BackgroundScheduler()

    scheduler.add_job(run_downsample_minute, "interval", minutes=1)
    scheduler.add_job(run_downsample_hour, "interval", hours=1)
    scheduler.add_job(run_cleanup, "interval", hours=12)

    scheduler.start()


def run_downsample_minute():
    db = SessionLocal()
    downsample_minute(db)
    db.close()


def run_downsample_hour():
    db = SessionLocal()
    downsample_hour(db)
    db.close()


def run_cleanup():
    db = SessionLocal()
    cleanup_raw_data(db)
    db.close()