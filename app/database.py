from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def upsert_user(db: Session, uid: str, email: str):
    from app.models.user import User   # 👈 IMPORT TRỄ

    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        user = User(uid=uid, email=email)
        db.add(user)
    else:
        user.email = email
    db.commit()
