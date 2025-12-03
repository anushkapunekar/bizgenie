"""
SQLAlchemy database models.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Business(Base):
    """Business model."""
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    services = Column(JSON, default=list)  # List of service names
    working_hours = Column(JSON, default=dict)  # Dict with day: {open, close}
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    documents = relationship("Document", back_populates="business", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="business", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="business", cascade="all, delete-orphan")


class Document(Base):
    """Document model for storing business documents."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Supabase URL or local path
    file_type = Column(String(50), default="pdf")
    document_metadata = Column(JSON, default=dict)  # Additional metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    business = relationship("Business", back_populates="documents")


class Appointment(Base):
    """Appointment model."""
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    customer_name = Column(String(200), nullable=False)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    appointment_date = Column(DateTime(timezone=True), nullable=False, index=True)
    service = Column(String(200), nullable=True)
    status = Column(String(50), default="scheduled")  # pending, confirmed, cancelled, completed
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    business = relationship("Business", back_populates="appointments")


class Lead(Base):
    """Lead model for tracking potential customers."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True, index=True)
    source = Column(String(100), default="chat")  # chat, website, referral, etc.
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    business = relationship("Business", back_populates="leads")

