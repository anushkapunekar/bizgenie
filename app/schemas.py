"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, time
from enum import Enum


class BusinessCreate(BaseModel):
    """Schema for business registration."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    services: List[str] = []
    working_hours: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="Format: {'monday': {'open': '09:00', 'close': '17:00'}, ...}"
    )
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class BusinessUpdate(BaseModel):
    """Schema for business profile updates."""
    name: Optional[str] = None
    description: Optional[str] = None
    services: Optional[List[str]] = None
    working_hours: Optional[Dict[str, Dict[str, str]]] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class BusinessLoginRequest(BaseModel):
    """Schema for logging into an existing business profile."""
    business_id: Optional[int] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    name: Optional[str] = None

    @model_validator(mode="after")
    def validate_identifier(self) -> "BusinessLoginRequest":
        if not any(
            getattr(self, field) for field in ("business_id", "contact_email", "contact_phone", "name")
        ):
            raise ValueError(
                "At least one identifier (business_id, contact_email, contact_phone, or name) is required."
            )
        return self


class BusinessResponse(BaseModel):
    """Schema for business response."""
    id: int
    name: str
    description: Optional[str]
    services: List[str]
    working_hours: Dict[str, Dict[str, str]]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentUpload(BaseModel):
    """Schema for document upload."""
    business_id: int
    filename: str
    file_type: str = "pdf"
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: int
    business_id: int
    filename: str
    file_path: str
    file_type: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Schema for chat request."""
    business_id: int
    user_name: str = Field(..., min_length=1)
    user_message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Schema for chat response."""
    reply: str
    tool_actions: List[Dict[str, Any]] = Field(default_factory=list)
    conversation_id: str
    intent: Optional[str] = None


class AppointmentCreate(BaseModel):
    business_id: int
    customer_name: str
    customer_email: str | None = None
    date: str  # Format: YYYY-MM-DD
    time: str  # Format: HH:MM


class AppointmentRequest(BaseModel):
    """Schema for appointment request."""
    business_id: int
    customer_name: str
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None
    preferred_date: str
    preferred_time: str
    service: Optional[str] = None
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    """Schema for appointment response."""
    id: int
    business_id: int
    customer_name: str
    customer_email: Optional[str]
    customer_phone: Optional[str]
    appointment_date: datetime
    service: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class LeadCreate(BaseModel):
    """Schema for lead creation."""
    business_id: int
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    source: str = "chat"
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    """Schema for lead response."""
    id: int
    business_id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    source: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
        orm_mode =True
        

