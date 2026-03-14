from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

from app.routers.device import router as device_router
from app.routers.health_data import router as health_data_router
from app.routers.alert import router as alert_router
from app.routers.iot import router as iot_router
from app.routers.device_stats import router as stats_router
from app.core.scheduler import start_scheduler

import app.core.firebase  # init Firebasex
import app.models

app = FastAPI(
    title="Health Monitor API",
    version="0.1.0"
)

# 🔥 THÊM CORS NGAY SAU KHI TẠO app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev thôi
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    start_scheduler()

app.include_router(device_router)
app.include_router(health_data_router)
app.include_router(alert_router)
app.include_router(iot_router)
app.include_router(stats_router)

@app.get("/")
def root():
    return {"status": "API Server is running"}

