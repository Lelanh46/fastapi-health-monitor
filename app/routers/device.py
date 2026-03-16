from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app import models, schemas
from app.auth.auth import get_current_user
from sqlalchemy.exc import IntegrityError
from app.schemas.device import DeviceRegisterRequest
from app.models.device import Device
from app.core.firebase import get_db_ref
from app.schemas.device_share import ShareDeviceRequest
from app.services.realtime_service import push_user_device
from app.schemas.health_data import HealthDataResponse
from app.models.device_member import DeviceMember
from sqlalchemy import text
from app.schemas.device_revoke import RevokeDeviceRequest

router = APIRouter(prefix="/devices", tags=["Devices"])

# 1️⃣ STATIC ROUTES (luôn đặt trên)
@router.post("/register")
def register_device(
    payload: DeviceRegisterRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    device = (
        db.query(Device)
        .filter(Device.device_code == payload.device_code)
        .first()
    )

    # 🔥 nếu device chưa tồn tại → tạo mới
    if not device:
        device = Device(
            device_code=payload.device_code,
            device_uid=None,
            device_name=None,
            owner_uid=None
        )
        db.add(device)
        db.commit()
        db.refresh(device)

    # ❗ nếu device đã có owner → không cho đăng ký
    if device.owner_uid is not None:
        raise HTTPException(
            status_code=400,
            detail="Device already registered"
        )

    # 1️⃣ PostgreSQL
    device.device_uid = payload.device_uid
    device.device_name = payload.device_name
    device.owner_uid = user["uid"]

    db.commit()
    db.refresh(device)

    # 2️⃣ Firebase Realtime
    user_ref = get_db_ref(f"users/{user['uid']}/devices/{payload.device_uid}")
    user_ref.set({
        "nickname": payload.device_name,
        "role": "owner",
        "createdAt": datetime.utcnow().isoformat()
    })

    device_ref = get_db_ref(f"devices/{payload.device_uid}")
    device_ref.set({
        "device_code": device.device_code,
        "owner": user["uid"],
        "status": "online",
        "createdAt": datetime.utcnow().isoformat()
    })

    return {
        "message": "Device registered successfully",
        "device_code": device.device_code,
        "device_uid": device.device_uid
    }




@router.get("", response_model=List[schemas.Device])
def get_devices(user=Depends(get_current_user), db: Session = Depends(get_db)):
    owned = db.query(Device).filter(Device.owner_uid == user["uid"])
    shared = (
        db.query(Device)
        .join(models.DeviceMember)
        .filter(models.DeviceMember.user_uid == user["uid"])
    )
    return owned.union(shared).all()

@router.post("/share")
def share_device(
    payload: ShareDeviceRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    device = db.query(Device).filter(
        Device.device_uid == payload.device_uid
    ).first()
    if not device:
        raise HTTPException(404, "Device not found")

    if device.owner_uid != user["uid"]:
        raise HTTPException(403, "Only owner can share device")

    # 🔍 tìm user theo email
    target_user = db.execute(
        text("SELECT uid, email FROM users WHERE email = :email"),
        {"email": payload.target_email}
    ).fetchone()

    if not target_user:
        raise HTTPException(404, "User not found")

    exists = (
        db.query(DeviceMember)
        .filter_by(
            device_id=device.id,
            user_uid=target_user.uid
        )
        .first()
    )
    if exists:
        raise HTTPException(400, "User already has access")

    member = DeviceMember(
        device_id=device.id,
        user_uid=target_user.uid,
        role=payload.role
    )
    db.add(member)
    db.commit()

    push_user_device(
        user_uid=target_user.uid,
        device_uid=device.device_uid,
        role=payload.role
    )

    return {
        "status": "shared",
        "email": target_user.email
    }

@router.post("/revoke")
def revoke_device(
    payload: RevokeDeviceRequest,   # ✅ ĐÚNG
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    device = (
        db.query(Device)
        .filter(Device.device_uid == payload.device_uid)
        .first()
    )
    if not device:
        raise HTTPException(404, "Device not found")

    if device.owner_uid != user["uid"]:
        raise HTTPException(403, "Only owner can revoke")

    member = (
        db.query(DeviceMember)
        .filter_by(
            device_id=device.id,
            user_uid=payload.target_user_uid
        )
        .first()
    )
    if not member:
        raise HTTPException(400, "User has no access")

    db.delete(member)
    db.commit()

    # 🔥 XÓA QUYỀN TRÊN FIREBASE
    push_user_device(
        user_uid=payload.target_user_uid,
        device_uid=device.device_uid,
        role=None
    )

    return {"status": "revoked"}

@router.get("/{device_uid}/members")
def list_device_members(
    device_uid: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter_by(device_uid=device_uid).first()
    if not device:
        raise HTTPException(404)

    if device.owner_uid != user["uid"]:
        raise HTTPException(403)

    rows = db.execute(text("""
        SELECT u.uid, u.email, dm.role, dm.created_at
        FROM device_members dm
        JOIN users u ON u.uid = dm.user_uid
        WHERE dm.device_id = :device_id
    """), {"device_id": device.id}).fetchall()

    return [
        {
            "user_uid": r.uid,
            "email": r.email,
            "role": r.role,
            "created_at": r.created_at
        }
        for r in rows
    ]

@router.get(
    "/{device_id}/health-history",
    response_model=List[HealthDataResponse]
)
def get_history(
    device_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(404)

    if device.owner_uid != user["uid"]:
        member = db.query(DeviceMember).filter_by(
            device_id=device.id,
            user_uid=user["uid"]
        ).first()
        if not member:
            raise HTTPException(403)

    return (
        db.query(models.HealthData)   # ✅ ORM OBJECT
        .filter(models.HealthData.device_id == device.id)
        .order_by(models.HealthData.recorded_at.desc())
        .limit(200)
        .all()
    )
