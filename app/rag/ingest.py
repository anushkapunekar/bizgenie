"""
Document ingestion pipeline for RAG.
"""
import os
from typing import List, Dict, Any, Optional
from PyPDF2 import PdfReader
import structlog
from app.rag.vectorstore import vector_store

logger = structlog.get_logger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        file_path: Path to PDF file
    
    Returns:
        Extracted text
    """
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        logger.info("Extracted text from PDF", file_path=file_path, pages=len(reader.pages))
        return text
    except Exception as e:
        logger.error("Error extracting text from PDF", file_path=file_path, error=str(e))
        raise


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into chunks for embedding.
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk
        chunk_overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    """
    # TODO: Use LangChain's text splitter for better chunking
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - chunk_overlap
    return chunks


def ingest_document(
    business_id: int,
    file_path: str,
    filename: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Ingest a document into the vector store.
    
    Args:
        business_id: Business identifier
        file_path: Path to document file
        filename: Original filename
        metadata: Additional metadata
    
    Returns:
        True if successful
    """
    try:
        # Extract text based on file type
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext == ".pdf":
            text = extract_text_from_pdf(file_path)
        else:
            # TODO: Support other file types (docx, txt, etc.)
            logger.warning("Unsupported file type", file_ext=file_ext)
            return False
        
        # Chunk the text
        chunks = chunk_text(text)
        
        # Prepare documents for vector store
        documents = []
        for i, chunk in enumerate(chunks):
            documents.append({
                "text": chunk,
                "metadata": {
                    "filename": filename,
                    "chunk_index": i,
                    "business_id": business_id,
                    **(metadata or {})
                },
                "id": f"{business_id}_{filename}_{i}"
            })
        
        # Add to vector store
        success = vector_store.add_documents(business_id, documents)
        
        if success:
            logger.info(
                "Document ingested successfully",
                business_id=business_id,
                filename=filename,
                chunks=len(chunks)
            )
        
        return success
    except Exception as e:
        logger.error(
            "Error ingesting document",
            business_id=business_id,
            file_path=file_path,
            error=str(e)
        )
        return False


def ingest_text(
    business_id: int,
    text: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Ingest raw text into the vector store.
    
    Args:
        business_id: Business identifier
        text: Text content
        metadata: Additional metadata
    
    Returns:
        True if successful
    """
    try:
        chunks = chunk_text(text)
        
        documents = []
        for i, chunk in enumerate(chunks):
            documents.append({
                "text": chunk,
                "metadata": {
                    "chunk_index": i,
                    "business_id": business_id,
                    **(metadata or {})
                },
                "id": f"{business_id}_text_{i}"
            })
        
        return vector_store.add_documents(business_id, documents)
    except Exception as e:
        logger.error("Error ingesting text", business_id=business_id, error=str(e))
        return False

