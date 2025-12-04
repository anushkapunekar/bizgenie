from fastapi import APIRouter, HTTPException
import requests
from app.rag.vectorstore import vector_store


router = APIRouter(prefix="/google-drive", tags=["GoogleDrive"])

GOOGLE_FILE_URL = "https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"


@router.post("/upload")
async def upload_from_drive(payload: dict):
    business_id = payload["business_id"]
    file_id = payload["file_id"]
    filename = payload["filename"]
    access_token = payload["access_token"]

    # Download from drive
    url = GOOGLE_FILE_URL.format(file_id=file_id)
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(400, "Failed to download file from Drive.")

    file_bytes = resp.content

    # Add to RAG vectorstore
    vector_store.add_document(
        business_id=business_id,
        filename=filename,
        content_bytes=file_bytes,
        metadata={"source": "google_drive", "filename": filename}
    )

    return {"status": "ok", "filename": filename}
