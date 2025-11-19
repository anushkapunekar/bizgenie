"""
Business API routes for registration and management.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List
import os
import uuid
import structlog
import PyPDF2

from app.database import get_db
from app.models import Business, Document
from app.config import get_settings
from app.tools.whatsapp_mcp import send_whatsapp_message
from app.tools.email_mcp import send_email
from app.schemas import (
    BusinessCreate,
    BusinessUpdate,
    BusinessResponse,
    BusinessLoginRequest,
    DocumentResponse
)
from app.rag.vectorstore import vector_store   # <-- DIRECT RAG INGESTION

logger = structlog.get_logger(__name__)
settings = get_settings()


async def notify_document_upload(business: Business, document_name: str) -> None:
    """Send WhatsApp/Email notifications after a document upload."""
    message = (
        f"New document uploaded for {business.name}: {document_name}. "
        "The assistant will now use it for customer answers."
    )

    if settings.EMAIL_MCP_ENABLED and business.contact_email:
        try:
            result = await send_email(
                to=business.contact_email,
                subject=f"New document uploaded: {document_name}",
                body=message,
            )
            logger.info("business.doc_email_notification", result=result)
        except Exception as exc:
            logger.warning("business.doc_email_failed", error=str(exc))

    if settings.WHATSAPP_MCP_ENABLED and business.contact_phone:
        try:
            result = await send_whatsapp_message(
                to=business.contact_phone,
                message=message,
            )
            logger.info("business.doc_whatsapp_notification", result=result)
        except Exception as exc:
            logger.warning("business.doc_whatsapp_failed", error=str(exc))

router = APIRouter(prefix="/business", tags=["business"])


# -------------------------
# REGISTER BUSINESS
# -------------------------
@router.post("/register", response_model=BusinessResponse)
async def register_business(
    business_data: BusinessCreate,
    db: Session = Depends(get_db)
) -> BusinessResponse:

    try:
        business = Business(
            name=business_data.name,
            description=business_data.description,
            services=business_data.services,
            working_hours=business_data.working_hours,
            contact_email=business_data.contact_email,
            contact_phone=business_data.contact_phone
        )
        
        db.add(business)
        db.commit()
        db.refresh(business)

        logger.info("Business registered", business_id=business.id, name=business.name)
        return BusinessResponse.model_validate(business)

    except Exception as e:
        logger.error("Error registering business", error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error registering business: {str(e)}")


# -------------------------
# UPDATE BUSINESS
# -------------------------
@router.patch("/update/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: int,
    business_data: BusinessUpdate,
    db: Session = Depends(get_db)
) -> BusinessResponse:

    try:
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")

        update_data = business_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(business, field, value)

        db.commit()
        db.refresh(business)

        logger.info("Business updated", business_id=business_id)
        return BusinessResponse.model_validate(business)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating business", business_id=business_id, error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating business: {str(e)}")


# -------------------------
# GET BUSINESS
# -------------------------
@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(business_id: int, db: Session = Depends(get_db)) -> BusinessResponse:

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    return BusinessResponse.from_orm(business)


# -------------------------
# LOGIN BUSINESS
# -------------------------
@router.post("/login", response_model=BusinessResponse)
async def login_business(
    request: BusinessLoginRequest,
    db: Session = Depends(get_db)
) -> BusinessResponse:

    try:
        filters = []
        if request.business_id:
            filters.append(Business.id == request.business_id)
        if request.contact_email:
            filters.append(func.lower(Business.contact_email) == request.contact_email.lower())
        if request.contact_phone:
            filters.append(Business.contact_phone == request.contact_phone)
        if request.name:
            filters.append(func.lower(Business.name) == request.name.lower())

        if not filters:
            raise HTTPException(status_code=400, detail="Provide at least one identifier to log in.")

        business = (
            db.query(Business)
            .filter(or_(*filters))
            .order_by(Business.updated_at.desc())
            .first()
        )

        if not business:
            raise HTTPException(status_code=404, detail="Business not found with provided details.")

        logger.info("Business login successful", business_id=business.id)
        return BusinessResponse.model_validate(business)

    except Exception as e:
        logger.error("Error logging in business", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error logging in business: {str(e)}")


# -------------------------
# UPLOAD DOCUMENT + INGEST INTO RAG
# -------------------------
@router.post("/upload-docs", response_model=DocumentResponse)
async def upload_documents(
    business_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> DocumentResponse:

    try:
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")

        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        content = await file.read()
        file_size = len(content)

        # ---------- SAVE FILE LOCALLY ----------
        storage_path = os.getenv("LOCAL_STORAGE_PATH", "./storage/documents")
        os.makedirs(storage_path, exist_ok=True)

        file_id = str(uuid.uuid4())
        saved_filename = f"{business_id}_{file_id}.pdf"
        file_path = os.path.join(storage_path, saved_filename)

        with open(file_path, "wb") as f:
            f.write(content)

        logger.info("File saved locally", file_path=file_path)

        # ---------- SAVE RECORD IN DATABASE ----------
        document = Document(
            business_id=business_id,
            filename=file.filename,
            file_path=file_path,
            file_type="pdf",
            document_metadata={"size": file_size}
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        # ---------- RAG INGESTION ----------
        try:
            extracted_text = ""
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    extracted_text += page.extract_text() or ""

            if extracted_text.strip():
                vector_store.add_documents(
                    business_id=business_id,
                    documents=[{
                        "id": str(document.id),
                        "text": extracted_text,
                        "metadata": {
                            "filename": file.filename,
                            "document_id": document.id
                        }
                    }]
                )
                logger.info("Document ingested into vector store", document_id=document.id)
            else:
                logger.warning("PDF had no extractable text", document_id=document.id)

        except Exception as e:
            logger.error("RAG ingestion failed", document_id=document.id, error=str(e))

        # ---------- NOTIFICATIONS ----------
        await notify_document_upload(business, document.filename)

        # ---------- RESPONSE ----------
        return DocumentResponse(
            id=document.id,
            business_id=document.business_id,
            filename=document.filename,
            file_path=document.file_path,
            file_type=document.file_type,
            created_at=document.created_at,
            metadata=document.document_metadata or {}
        )

    except Exception as e:
        logger.error("Error uploading document", error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")


# -------------------------
# GET ALL DOCUMENTS
# -------------------------
@router.get("/{business_id}/documents", response_model=List[DocumentResponse])
async def get_business_documents(
    business_id: int,
    db: Session = Depends(get_db)
) -> List[DocumentResponse]:

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    documents = db.query(Document).filter(Document.business_id == business_id).all()

    result = []
    for doc in documents:
        result.append(DocumentResponse(
            id=doc.id,
            business_id=doc.business_id,
            filename=doc.filename,
            file_path=doc.file_path,
            file_type=doc.file_type,
            created_at=doc.created_at,
            metadata=getattr(doc, "document_metadata", {}) or {}
        ))

    return result
