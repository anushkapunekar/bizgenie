from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Appointment, Business
from app.schemas import AppointmentCreate, AppointmentResponse
from app.tools.email_mcp import send_email
from app.tools.calendar_mcp import create_event

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("/", response_model=AppointmentResponse)
async def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):

    business = db.query(Business).filter(Business.id == payload.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # 1) Build appointment datetime
    try:
        appt_dt = datetime.strptime(f"{payload.date} {payload.time}", "%Y-%m-%d %H:%M")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date/time format")

    # 2) Save appointment in DB
    appt = Appointment(
        business_id=payload.business_id,
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        customer_phone=None,
        appointment_date=appt_dt,
        service=None,
        status="scheduled",
        notes=None,
    )

    db.add(appt)
    db.commit()
    db.refresh(appt)

    # 3) Customer confirmation email
    if payload.customer_email:
        try:
            await send_email(
                to=payload.customer_email,
                subject="Appointment Confirmed",
                body=f"Your appointment with {business.name} is booked on {payload.date} at {payload.time}.",
            )
        except Exception as exc:
            print("Customer email failed:", exc)

    # 4) Calendar helper (email-based)
    try:
        end_dt = appt_dt + timedelta(hours=1)
        await create_event(
            title=f"Appointment - {payload.customer_name}",
            description=f"Online booking via BizGenie for {business.name}",
            start_dt=appt_dt.isoformat(),
            end_dt=end_dt.isoformat(),
            location=None,
            attendees_emails=[payload.customer_email] if payload.customer_email else [],
            send_via_email=True,
            send_via_whatsapp=False,
        )
    except Exception as exc:
        print("Calendar helper failed:", exc)

    return appt
