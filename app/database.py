"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

# Prefer a simple local SQLite database by default to avoid external DB setup.
# If you really want PostgreSQL, set USE_SQLITE=false in your .env and provide a DATABASE_URL.
use_sqlite = os.getenv("USE_SQLITE", "true").lower() == "true"
if use_sqlite:
    DATABASE_URL = "sqlite:///./bizgenie.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/bizgenie")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency for getting database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    TODO: Run migrations with Alembic instead of create_all in production.
    """
    # Import all models to ensure they're registered with Base
    from app.models import Business, Document, Appointment, Lead
    
    # Create all tables
    Base.metadata.create_all(bind=engine)

