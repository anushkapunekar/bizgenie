"""
Email MCP Tool for sending emails.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import structlog
from dotenv import load_dotenv

load_dotenv()

logger = structlog.get_logger(__name__)


def send_email(
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send an email via SMTP.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (plain text)
        from_email: Sender email (defaults to SMTP_USER)
    
    Returns:
        Dict with success status and response data
    """
    try:
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        
        if not smtp_user or not smtp_password:
            logger.warning("SMTP credentials not configured")
            # TODO: In production, raise an error
            return {
                "success": False,
                "error": "SMTP credentials not configured",
                "message": "Email integration not set up"
            }
        
        from_addr = from_email or smtp_user
        
        # Create message
        msg = MIMEMultipart()
        msg["From"] = from_addr
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        # Send email
        # TODO: Use async email sending in production
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        logger.info("Email sent successfully", to=to, subject=subject)
        
        return {
            "success": True,
            "to": to,
            "subject": subject,
            "status": "sent"
        }
    except Exception as e:
        logger.error("Error sending email", to=to, error=str(e))
        return {
            "success": False,
            "error": str(e)
        }

