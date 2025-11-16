"""
Calendar MCP Tool for appointment scheduling.
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import structlog
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Appointment, Business
from dotenv import load_dotenv

load_dotenv()

logger = structlog.get_logger(__name__)


def get_available_slots(
    business_id: int,
    date: str,
    duration_minutes: int = 60,
    db: Optional[Session] = None
) -> List[Dict[str, Any]]:
    """
    Get available appointment slots for a business on a given date.
    
    Args:
        business_id: Business identifier
        date: Date in YYYY-MM-DD format
        duration_minutes: Duration of each slot in minutes
        db: Database session (optional)
    
    Returns:
        List of available time slots
    """
    try:
        if db is None:
            # TODO: Get db from dependency injection
            db_gen = get_db()
            db = next(db_gen)
        
        # Get business working hours
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            logger.warning("Business not found", business_id=business_id)
            return []
        
        # Parse date
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        day_name = target_date.strftime("%A").lower()
        
        # Get working hours for the day
        working_hours = business.working_hours.get(day_name, {})
        if not working_hours:
            logger.info("Business closed on this day", business_id=business_id, day=day_name)
            return []
        
        open_time = working_hours.get("open", "09:00")
        close_time = working_hours.get("close", "17:00")
        
        # Parse times
        open_hour, open_min = map(int, open_time.split(":"))
        close_hour, close_min = map(int, close_time.split(":"))
        
        start_datetime = datetime.combine(target_date, datetime.min.time().replace(hour=open_hour, minute=open_min))
        end_datetime = datetime.combine(target_date, datetime.min.time().replace(hour=close_hour, minute=close_min))
        
        # Get existing appointments
        existing_appointments = db.query(Appointment).filter(
            Appointment.business_id == business_id,
            Appointment.appointment_date >= start_datetime,
            Appointment.appointment_date < end_datetime + timedelta(days=1),
            Appointment.status.in_(["pending", "confirmed"])
        ).all()
        
        booked_times = {apt.appointment_date for apt in existing_appointments}
        
        # Generate slots
        slots = []
        current_time = start_datetime
        
        while current_time + timedelta(minutes=duration_minutes) <= end_datetime:
            if current_time not in booked_times:
                slots.append({
                    "time": current_time.strftime("%H:%M"),
                    "datetime": current_time.isoformat(),
                    "available": True
                })
            current_time += timedelta(minutes=duration_minutes)
        
        logger.info(
            "Generated available slots",
            business_id=business_id,
            date=date,
            slots_count=len(slots)
        )
        
        return slots
    except Exception as e:
        logger.error("Error getting available slots", business_id=business_id, date=date, error=str(e))
        return []


def generate_appointment_confirmation(
    appointment_id: int,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Generate appointment confirmation message.
    
    Args:
        appointment_id: Appointment identifier
        db: Database session (optional)
    
    Returns:
        Confirmation message dict
    """
    try:
        if db is None:
            db_gen = get_db()
            db = next(db_gen)
        
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return {"success": False, "error": "Appointment not found"}
        
        business = appointment.business
        
        confirmation_message = f"""
Appointment Confirmed!

Business: {business.name}
Date: {appointment.appointment_date.strftime('%B %d, %Y at %I:%M %p')}
Service: {appointment.service or 'General Consultation'}
Customer: {appointment.customer_name}

Please arrive on time. If you need to reschedule, please contact us in advance.

Thank you!
{business.name}
"""
        
        logger.info("Generated appointment confirmation", appointment_id=appointment_id)
        
        return {
            "success": True,
            "message": confirmation_message.strip(),
            "appointment_id": appointment_id,
            "customer_email": appointment.customer_email,
            "customer_phone": appointment.customer_phone
        }
    except Exception as e:
        logger.error("Error generating appointment confirmation", appointment_id=appointment_id, error=str(e))
        return {"success": False, "error": str(e)}

