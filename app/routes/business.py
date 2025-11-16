"""
Business API routes for registration and management.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import structlog
from app.database import get_db
from app.models import Business, Document
from app.schemas import (
    BusinessCreate,
    BusinessUpdate,
    BusinessResponse,
    DocumentResponse
)
from app.rag.ingest import ingest_document

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/business", tags=["business"])


@router.post("/register", response_model=BusinessResponse)
async def register_business(
    business_data: BusinessCreate,
    db: Session = Depends(get_db)
) -> BusinessResponse:
    """
    Register a new business.
    
    Args:
        business_data: Business registration data
        db: Database session
    
    Returns:
        Created business information
    """
    try:
        # Create business
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


@router.patch("/update/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: int,
    business_data: BusinessUpdate,
    db: Session = Depends(get_db)
) -> BusinessResponse:
    """
    Update business profile.
    
    Args:
        business_id: Business identifier
        business_data: Business update data
        db: Database session
    
    Returns:
        Updated business information
    """
    try:
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        # Update fields
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


@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: int,
    db: Session = Depends(get_db)
) -> BusinessResponse:
    """
    Get business information.
    
    Args:
        business_id: Business identifier
        db: Database session
    
    Returns:
        Business information
    """
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    return BusinessResponse.from_orm(business)


@router.post("/upload-docs", response_model=DocumentResponse)
async def upload_documents(
    business_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> DocumentResponse:
    """
    Upload documents (PDFs) for a business.
    
    Args:
        business_id: Business identifier
        file: Uploaded file
        db: Database session
    
    Returns:
        Document information
    """
    try:
        # Verify business exists
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        # Check file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Determine storage location
        use_local_storage = os.getenv("USE_LOCAL_STORAGE", "true").lower() == "true"
        
        if use_local_storage:
            # Local storage
            storage_path = os.getenv("LOCAL_STORAGE_PATH", "./storage/documents")
            os.makedirs(storage_path, exist_ok=True)
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file.filename)[1]
            saved_filename = f"{business_id}_{file_id}{file_extension}"
            file_path = os.path.join(storage_path, saved_filename)
            
            # Save file
            with open(file_path, "wb") as f:
                f.write(content)
            
            logger.info("File saved locally", business_id=business_id, file_path=file_path)
            
        else:
            # TODO: Implement Supabase storage
            # from supabase import create_client, Client
            # supabase_url = os.getenv("SUPABASE_URL")
            # supabase_key = os.getenv("SUPABASE_KEY")
            # supabase: Client = create_client(supabase_url, supabase_key)
            # 
            # file_id = str(uuid.uuid4())
            # saved_filename = f"{business_id}/{file_id}_{file.filename}"
            # 
            # response = supabase.storage.from_(os.getenv("SUPABASE_BUCKET", "documents")).upload(
            #     saved_filename, content
            # )
            # file_path = response.get("path")
            
            raise HTTPException(status_code=501, detail="Supabase storage not yet implemented")
        
        # Create document record
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
        
        # Ingest document into RAG system
        try:
            ingest_success = ingest_document(
                business_id=business_id,
                file_path=file_path,
                filename=file.filename,
                metadata={"document_id": document.id}
            )
            if ingest_success:
                logger.info("Document ingested into RAG", business_id=business_id, document_id=document.id)
        except Exception as e:
            logger.warning("Failed to ingest document", business_id=business_id, error=str(e))
        
        logger.info("Document uploaded", business_id=business_id, document_id=document.id)
        
        # Convert to response format
        doc_dict = {
            'id': document.id,
            'business_id': document.business_id,
            'filename': document.filename,
            'file_path': document.file_path,
            'file_type': document.file_type,
            'created_at': document.created_at
        }
        # Handle metadata field (model uses document_metadata)
        doc_dict['metadata'] = document.document_metadata or {}
        
        return DocumentResponse(**doc_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error uploading document", business_id=business_id, error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")


@router.get("/{business_id}/documents", response_model=List[DocumentResponse])
async def get_business_documents(
    business_id: int,
    db: Session = Depends(get_db)
) -> List[DocumentResponse]:
    """
    Get all documents for a business.
    
    Args:
        business_id: Business identifier
        db: Database session
    
    Returns:
        List of documents
    """
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    documents = db.query(Document).filter(Document.business_id == business_id).all()
    
    # Convert documents to response format, handling document_metadata field
    result = []
    for doc in documents:
        doc_dict = {
            'id': doc.id,
            'business_id': doc.business_id,
            'filename': doc.filename,
            'file_path': doc.file_path,
            'file_type': doc.file_type,
            'created_at': doc.created_at
        }
        # Handle metadata field (model uses document_metadata)
        if hasattr(doc, 'document_metadata'):
            doc_dict['metadata'] = doc.document_metadata or {}
        else:
            doc_dict['metadata'] = getattr(doc, 'metadata', {}) or {}
        result.append(DocumentResponse(**doc_dict))
    return result

