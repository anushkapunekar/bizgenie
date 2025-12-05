"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# ---------- BUSINESS ----------

class BusinessCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    services: List[str] = []
    working_hours: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="{'monday': {'open': '09:00', 'close': '17:00'}, ...}",
    )
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    services: Optional[List[str]] = None
    working_hours: Optional[Dict[str, Dict[str, str]]] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class BusinessLoginRequest(BaseModel):
    business_id: Optional[int] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    name: Optional[str] = None

    @model_validator(mode="after")
    def validate_identifier(self) -> "BusinessLoginRequest":
        if not any(
            getattr(self, field)
            for field in ("business_id", "contact_email", "contact_phone", "name")
        ):
            raise ValueError(
                "At least one identifier (business_id, contact_email, contact_phone, or name) is required."
            )
        return self


class BusinessResponse(BaseModel):
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


# ---------- DOCUMENTS ----------

class DocumentUpload(BaseModel):
    business_id: int
    filename: str
    file_type: str = "pdf"
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(BaseModel):
    id: int
    business_id: int
    filename: str
    file_path: str
    file_type: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- CHAT ----------

class ChatRequest(BaseModel):
    business_id: int
    user_name: str = Field(..., min_length=1)
    user_message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    tool_actions: List[Dict[str, Any]] = Field(default_factory=list)
    conversation_id: str
    intent: Optional[str] = None


# ---------- APPOINTMENTS ----------

class AppointmentCreate(BaseModel):
    business_id: int
    customer_name: str
    customer_email: Optional[str] = None
    date: str  # YYYY-MM-DD
    time: str  # HH:MM


class AppointmentResponse(BaseModel):
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


# ---------- LEADS ----------

class LeadCreate(BaseModel):
    business_id: int
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    source: str = "chat"
    notes: Optional[str] = None


class LeadResponse(BaseModel):
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
        orm_mode = True
