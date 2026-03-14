from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.health_data import HealthData


def cleanup_raw_data(db: Session):

    cutoff = datetime.utcnow() - timedelta(days=7)

    db.query(HealthData).filter(
        HealthData.measured_at < cutoff
    ).delete(synchronize_session=False)

    db.commit()