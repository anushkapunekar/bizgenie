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

    # ---------------------------------------
    # 1) Combine date + time → datetime object
    # ---------------------------------------
    try:
        appt_dt = datetime.strptime(f"{payload.date} {payload.time}", "%Y-%m-%d %H:%M")
    except:
        raise HTTPException(status_code=400, detail="Invalid date/time format")

    # ---------------------------------------
    # 2) Save appointment correctly
    # ---------------------------------------
    appt = Appointment(
        business_id=payload.business_id,
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        appointment_date=appt_dt,
        service=None,
        customer_phone=None,
        notes=None,
    )

    db.add(appt)
    db.commit()
    db.refresh(appt)

    # ---------------------------------------
    # 3) Send email confirmation (customer)
    # ---------------------------------------
    if payload.customer_email:
        try:
            await send_email(
                to=payload.customer_email,
                subject="Appointment Confirmed",
                body=(
                    f"Your appointment with {business.name} is booked for "
                    f"{appt_dt.strftime('%Y-%m-%d at %H:%M')}."
                )
            )
        except Exception as exc:
            print("Email sending failed:", exc)

    # ---------------------------------------
    # 4) Add to Google Calendar (business)
    # ---------------------------------------
    try:
        start_iso = appt_dt.isoformat()
        end_iso = (appt_dt + timedelta(hours=1)).isoformat()

        await create_event(
            title=f"Appointment - {payload.customer_name}",
            description=f"Online booking for {business.name}",
            start_dt=start_iso,
            end_dt=end_iso,
            location=None,
            attendees_emails=[payload.customer_email] if payload.customer_email else [],
            send_via_email=True,
            send_via_whatsapp=False,
        )
    except Exception as exc:
        print("Calendar event failed:", exc)

    # ---------------------------------------
    # 5) RETURN correct AppointmentResponse
    # ---------------------------------------
    return AppointmentResponse(
        id=appt.id,
        business_id=appt.business_id,
        customer_name=appt.customer_name,
        customer_email=appt.customer_email,
        customer_phone=appt.customer_phone,
        appointment_date=appt.appointment_date,
        service=appt.service,
        status=appt.status,
        created_at=appt.created_at,
    )
