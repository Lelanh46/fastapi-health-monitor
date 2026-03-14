from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.models.health_data import HealthData
from app.models.health_data_agg import HealthDataAgg


def downsample_minute(db: Session):

    rows = (
        db.query(
            HealthData.device_id,
            func.date_trunc("minute", HealthData.measured_at).label("bucket"),
            func.avg(HealthData.heart_rate).label("avg_hr"),
            func.avg(HealthData.spo2).label("avg_spo2"),
            func.avg(HealthData.temperature).label("avg_temp"),
            func.avg(HealthData.humidity).label("avg_humidity")
        )
        .filter(
            HealthData.measured_at >= datetime.utcnow() - timedelta(minutes=1)
        )
        .group_by(
            HealthData.device_id,
            func.date_trunc("minute", HealthData.measured_at)
        )
        .all()
    )

    for r in rows:

        exists = db.query(HealthDataAgg).filter(
            HealthDataAgg.device_id == r.device_id,
            HealthDataAgg.bucket == "minute",
            HealthDataAgg.bucket_time == r.bucket
        ).first()

        if not exists:
            db.add(
                HealthDataAgg(
                    device_id=r.device_id,
                    bucket="minute",
                    bucket_time=r.bucket,
                    avg_hr=r.avg_hr,
                    avg_spo2=r.avg_spo2,
                    avg_temp=r.avg_temp,
                    avg_humidity=r.avg_humidity
                )
            )

    db.commit()


def downsample_hour(db: Session):

    rows = (
        db.query(
            HealthData.device_id,
            func.date_trunc("hour", HealthData.measured_at).label("bucket"),
            func.avg(HealthData.heart_rate).label("avg_hr"),
            func.avg(HealthData.spo2).label("avg_spo2"),
            func.avg(HealthData.temperature).label("avg_temp"),
            func.avg(HealthData.humidity).label("avg_humidity")
        )
        .filter(
            HealthData.measured_at >= datetime.utcnow() - timedelta(hours=1)
        )
        .group_by(
            HealthData.device_id,
            func.date_trunc("hour", HealthData.measured_at)
        )
        .all()
    )

    for r in rows:
        exists = db.query(HealthDataAgg).filter(
        HealthDataAgg.device_id == r.device_id,
        HealthDataAgg.bucket == "hour",
        HealthDataAgg.bucket_time == r.bucket
    ).first()

    if not exists:
        db.add(
            HealthDataAgg(
                device_id=r.device_id,
                bucket="hour",
                bucket_time=r.bucket,
                avg_hr=r.avg_hr,
                avg_spo2=r.avg_spo2,
                avg_temp=r.avg_temp,
                avg_humidity=r.avg_humidity
            )
        )

    db.commit()