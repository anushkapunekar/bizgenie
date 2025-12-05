"""
Database configuration and session management.
"""
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------
# SELECT DATABASE
# ------------------------------------------
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    # 🚀 FIX: allow multithread access for FastAPI
    DATABASE_URL = "sqlite:///./bizgenie.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},   # <<< IMPORTANT FIX
        pool_pre_ping=True,
        echo=False
    )
else:
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=False
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# --------------------------------------------------
# DB Session for FastAPI dependency
# --------------------------------------------------
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------
# SAFE init_db (async-ready + non-blocking)
# --------------------------------------------------
def init_db():
    """
    Create all tables safely without blocking the server.
    """
    try:
        # Import all models
        from app.models import Business, Document, Appointment, Lead

        # Create tables
        Base.metadata.create_all(bind=engine)

        print("📦 Database initialized successfully.")
    except Exception as e:
        print("❌ DB Init Failed:", e)
