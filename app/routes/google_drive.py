from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import structlog

from app.rag.vectorstore import vector_store
from app.storage import save_pdf_file  # your existing local/supabase saver

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/google-drive", tags=["Google Drive"])


class DriveUploadRequest(BaseModel):
    business_id: int
    file_id: str
    filename: str
    access_token: str


# ----------------------------------------------------
# GOOGLE DRIVE: Download a PDF via access token
# ----------------------------------------------------
def download_pdf_from_drive(file_id: str, token: str) -> bytes:
    """
    Downloads a Google Drive file using the Picker access token.
    Only works for PDF because we restrict selection to PDF in frontend.
    """
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        logger.error("google_drive.download_fail", status=response.status_code, text=response.text)
        raise HTTPException(status_code=400, detail="Failed to download file from Google Drive")

    return response.content


# ----------------------------------------------------
# API — Upload From Google Drive Picker
# ----------------------------------------------------
@router.post("/upload")
async def upload_from_drive(payload: DriveUploadRequest):
    logger.info("google_drive.upload_request", payload=payload.model_dump())

    # Step 1: Download PDF
    pdf_bytes = download_pdf_from_drive(payload.file_id, payload.access_token)

    # Step 2: Save PDF to local storage or Supabase bucket
    saved_path = save_pdf_file(
        business_id=payload.business_id,
        filename=payload.filename,
        content=pdf_bytes,
    )

    # Step 3: Add document into vectorstore
    try:
        vector_store.add_document(
            business_id=payload.business_id,
            filename=payload.filename,
            content_bytes=pdf_bytes,
            metadata={"filename": payload.filename, "source": "google_drive"}
        )
    except Exception as e:
        logger.error("google_drive.vectorstore_error", error=str(e))

    return {
        "status": "success",
        "filename": payload.filename,
        "saved_path": saved_path,
    }
