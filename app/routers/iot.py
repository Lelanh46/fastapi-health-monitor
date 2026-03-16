from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Device, HealthData
from app.services.alert_service import analyze_and_create_alert
from app.services.realtime_service import push_latest_health
from app.schemas.iot import EspHealthPayload
from app.services.health_pipeline import clean_health_data
from app.services.seq_monitor import check_seq
from datetime import datetime
from app.services.seq_stats_service import update_seq_stats
from app.core.firebase import get_db_ref

router = APIRouter(prefix="/iot", tags=["IoT"])


@router.post("/push")
def esp_push_data(payload: EspHealthPayload, db: Session = Depends(get_db)):

    device = db.query(Device).filter(
        Device.device_code == payload.device_code
    ).first()

    if not device:
        raise HTTPException(404, "Device not found")

    # 📊 Detect missing seq
    seq_result = check_seq(device.id, payload.seq)
    update_seq_stats(db, device.id, payload.seq)

    if seq_result["missing"] > 0:
        print(f"⚠️ Missing {seq_result['missing']} samples from device {device.id}")

    if seq_result["duplicate"]:
        print(f"⚠️ Duplicate seq detected from device {device.id}")

    # 🧹 Clean data
    clean = clean_health_data(
        device.id,
        payload.dict(by_alias=True)
    )

    # 💾 Save DB
    health = HealthData(
        device_id=device.id,
        seq=payload.seq,
        heart_rate=clean["heart_rate"],
        spo2=clean["spo2"],
        temperature=(
            clean["temperature"]
            if clean["temperature"] is not None
            else payload.temperature
        ),
        gas_level=payload.gas_level,
        humidity=payload.humidity,
        blood_pressure=payload.blood_pressure,
        sent_at=(
        payload.sent_at.replace(tzinfo=None)
        if payload.sent_at
        else None
        ),
        measured_at=(
            payload.measured_at.replace(tzinfo=None)
            if payload.measured_at
            else datetime.utcnow()
        ),
        is_offline=payload.is_offline
    )

    db.add(health)

    # 🚨 Alerts
    analyze_and_create_alert(
        db,
        device.id,
        clean["heart_rate"],
        clean["spo2"],
        clean["temperature"],
        payload.humidity,
        payload.blood_pressure
    )

    db.commit()

    # 🔴 Push realtime
    if device.device_uid:
        push_latest_health(
        device_uid=device.device_uid,
        data={
            "heartRate": clean["heart_rate"],
            "spo2": clean["spo2"],
            "temperature": clean["temperature"] if clean["temperature"] is not None else payload.temperature,
            "gas": payload.gas_level,
            "humidity": payload.humidity,
            "bloodPressure": payload.blood_pressure
        }
    )

    return {"status": "ok"}

@router.post("/register")
def esp_register_device(payload: dict, db: Session = Depends(get_db)):

    device_code = payload.get("device_code")

    if not device_code:
        raise HTTPException(400, "device_code required")

    device = db.query(Device).filter(
        Device.device_code == device_code
    ).first()

    # nếu đã tồn tại
    if device:
        device_ref = get_db_ref(f"devices/{device_code}")
        device_ref.update({
            "status": "online",
            "lastSeen": datetime.utcnow().isoformat()
    })

    return {"status": "exists"}

    # tạo device mới trong Supabase
    new_device = Device(
        device_code=device_code,
        device_uid=device_code,   # 🔥 dùng luôn device_code
        owner_uid=None
    )

    db.add(new_device)
    db.commit()

    # 🔴 TẠO NODE FIREBASE REALTIME
    device_ref = get_db_ref(f"devices/{device_code}")
    device_ref.set({
        "device_code": device_code,
        "status": "online",
        "createdAt": datetime.utcnow().isoformat()
    })

    return {"status": "registered"}