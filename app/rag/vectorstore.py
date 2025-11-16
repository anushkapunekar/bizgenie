"""
ChromaDB vector store for RAG functionality.
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import structlog
from sentence_transformers import SentenceTransformer

load_dotenv()

logger = structlog.get_logger(__name__)


class VectorStore:
    """ChromaDB vector store wrapper for business-specific RAG."""
    
    def __init__(self):
        """Initialize ChromaDB client with free embeddings model."""
        persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Initialize free embeddings model (sentence-transformers)
        # Using all-MiniLM-L6-v2 - fast, free, good quality
        embedding_model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        try:
            self.embedding_model = SentenceTransformer(embedding_model_name)
            logger.info(
                "Embeddings model loaded",
                model=embedding_model_name,
                persist_directory=persist_directory
            )
        except Exception as e:
            logger.warning("Failed to load embeddings model, using ChromaDB default", error=str(e))
            self.embedding_model = None
        
        logger.info("ChromaDB client initialized", persist_directory=persist_directory)
    
    def get_collection(self, business_id: int):
        """Get or create a collection for a specific business."""
        collection_name = f"business_{business_id}"
        try:
            collection = self.client.get_collection(name=collection_name)
            logger.debug("Retrieved existing collection", business_id=business_id)
        except Exception:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"business_id": business_id}
            )
            logger.info("Created new collection", business_id=business_id)
        return collection
    
    def add_documents(
        self,
        business_id: int,
        documents: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None
    ) -> bool:
        """
        Add documents to the vector store.
        
        Args:
            business_id: Business identifier
            documents: List of dicts with 'text', 'metadata', and optionally 'id'
            embeddings: Optional pre-computed embeddings
        
        Returns:
            True if successful
        """
        try:
            collection = self.get_collection(business_id)
            
            texts = [doc.get("text", "") for doc in documents]
            metadatas = [doc.get("metadata", {}) for doc in documents]
            ids = [doc.get("id", f"doc_{business_id}_{i}") for i, doc in enumerate(documents)]
            
            # Use free sentence-transformers embeddings if available
            if self.embedding_model and not embeddings:
                try:
                    embeddings = self.embedding_model.encode(texts, show_progress_bar=False).tolist()
                    logger.debug("Generated embeddings using sentence-transformers", count=len(embeddings))
                except Exception as e:
                    logger.warning("Failed to generate embeddings, using ChromaDB default", error=str(e))
                    embeddings = None
            
            if embeddings:
                collection.add(
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids
                )
            else:
                # Fallback to ChromaDB default embeddings
                collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
            
            logger.info(
                "Added documents to vector store",
                business_id=business_id,
                count=len(documents)
            )
            return True
        except Exception as e:
            logger.error(
                "Error adding documents to vector store",
                business_id=business_id,
                error=str(e)
            )
            return False
    
    def query_documents(
        self,
        business_id: int,
        query: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query documents from the vector store.
        
        Args:
            business_id: Business identifier
            query: Search query
            n_results: Number of results to return
        
        Returns:
            List of relevant documents with metadata
        """
        try:
            collection = self.get_collection(business_id)
            
            # Generate query embedding if model available
            query_embedding = None
            if self.embedding_model:
                try:
                    query_embedding = self.embedding_model.encode([query], show_progress_bar=False).tolist()[0]
                except Exception as e:
                    logger.warning("Failed to generate query embedding", error=str(e))
            
            if query_embedding:
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results
                )
            else:
                results = collection.query(
                    query_texts=[query],
                    n_results=n_results
                )
            
            # Format results
            documents = []
            if results["documents"] and len(results["documents"][0]) > 0:
                for i, doc_text in enumerate(results["documents"][0]):
                    documents.append({
                        "text": doc_text,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else None
                    })
            
            logger.info(
                "Queried vector store",
                business_id=business_id,
                query=query,
                results_count=len(documents)
            )
            return documents
        except Exception as e:
            logger.error(
                "Error querying vector store",
                business_id=business_id,
                query=query,
                error=str(e)
            )
            return []
    
    def delete_collection(self, business_id: int) -> bool:
        """Delete a business's collection."""
        try:
            collection_name = f"business_{business_id}"
            self.client.delete_collection(name=collection_name)
            logger.info("Deleted collection", business_id=business_id)
            return True
        except Exception as e:
            logger.error("Error deleting collection", business_id=business_id, error=str(e))
            return False


# Global instance
vector_store = VectorStore()

