from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import os, uuid
from sqlalchemy import create_engine, Column, String, DateTime, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./claimshield.db")
ALLOWED_ORIGINS = [s.strip() for s in os.getenv("ALLOWED_ORIGINS", "*").split(",")]

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Vessel(Base):
    __tablename__ = "vessel"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    imo = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ClaimShield API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ['*'] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VesselIn(BaseModel):
    company_id: str
    name: str
    imo: Optional[str] = None

@app.get("/")
def root():
    return {"ok": True, "service": "ClaimShield API"}

@app.post("/vessels")
def create_vessel(v: VesselIn):
    db = SessionLocal()
    try:
        vid = str(uuid.uuid4())
        now = datetime.utcnow()
        db.execute(
            "INSERT INTO vessel(id, company_id, name, imo, created_at) VALUES (:id, :cid, :name, :imo, :ts)",
            {"id": vid, "cid": v.company_id, "name": v.name, "imo": v.imo, "ts": now},
        )
        db.commit()
        return {"id": vid, "created_at": now}
    finally:
        db.close()
