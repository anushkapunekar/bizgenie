from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Appointment, Business
from app.schemas import AppointmentCreate, AppointmentResponse
from app.tools.email_mcp import send_email
from app.tools.whatsapp_mcp import send_whatsapp_message

router = APIRouter(prefix="/appointments", tags=["appointments"])

@router.post("/", response_model=AppointmentResponse)
async def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):

    business = db.query(Business).filter(Business.id == payload.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # save appointment
    appt = Appointment(
        business_id=payload.business_id,
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        date=payload.date,
        time=payload.time,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    # send confirmation email
    if payload.customer_email:
        await send_email(
            to=payload.customer_email,
            subject="Appointment Confirmed",
            body=f"Your appointment is booked on {payload.date} at {payload.time}."
        )

    # send WhatsApp confirmation
    if business.contact_phone:
        await send_whatsapp_message(
            to=business.contact_phone,
            message=f"New appointment booked:\n{payload.customer_name}\n{payload.date} at {payload.time}"
        )

    return appt
