from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.device_stats import DeviceStats

router = APIRouter(prefix="/device-stats", tags=["Device Stats"])

@router.get("/{device_id}")
def get_device_stats(device_id: int, db: Session = Depends(get_db)):

    stats = db.query(DeviceStats).filter(
        DeviceStats.device_id == device_id
    ).first()

    if not stats:
        return {"message": "no stats"}

    loss_rate = 0
    if stats.total_packets > 0:
        loss_rate = stats.missing_packets / stats.total_packets

    return {
        "device_id": device_id,
        "total_packets": stats.total_packets,
        "missing_packets": stats.missing_packets,
        "duplicate_packets": stats.duplicate_packets,
        "loss_rate": loss_rate
    }