"""
Vector store used by BizGenie RAG.

The store *tries* to use ChromaDB (with persistent storage and high recall) but
falls back to a very small, pure-Python embedding store when native
dependencies such as `onnxruntime`, `hnswlib`, or `grpcio` are unavailable.

Both modes expose the same `add_documents` / `query_documents` interface.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
from dotenv import load_dotenv
import structlog

load_dotenv()

logger = structlog.get_logger(__name__)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


class VectorStore:
    """Wrapper that chooses between ChromaDB and a lightweight fallback store."""

    def __init__(self) -> None:
        self.client = None
        self.embedding_model = None
        self.mode: str = "simple"
        self.simple_dir = Path(os.getenv("SIMPLE_VECTOR_DIR", "./storage/vector_cache"))
        _ensure_dir(self.simple_dir)

        # ------------------------
        # Try to initialize Chroma
        # ------------------------
        persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        try:
            import chromadb  # type: ignore
            from chromadb.config import Settings  # type: ignore

            settings = Settings(
                chroma_db_impl="chromadb",
                persist_directory=persist_directory,
                anonymized_telemetry=False,
                allow_reset=True,
            )
            self.client = chromadb.Client(settings)
            self.mode = "chroma"
            logger.info("ChromaDB client initialized", persist_directory=persist_directory)
        except Exception as chroma_error:
            logger.error(
                "ChromaDB unavailable, falling back to simple vector store",
                error=str(chroma_error),
            )
            self.client = None
            self.mode = "simple"

        # ------------------------
        # Load embedding model
        # ------------------------
        try:
            from sentence_transformers import SentenceTransformer

            embedding_model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

            # Disable embeddings if set to "none"
            if embedding_model_name.lower() == "none":
                self.embedding_model = None
                logger.warning("Embeddings disabled via config (EMBEDDING_MODEL=none)")
            else:
                self.embedding_model = SentenceTransformer(embedding_model_name)
                logger.info("Embeddings model loaded", model=embedding_model_name)

        except Exception as e:
            logger.warning(
                "sentence-transformers unavailable; RAG will use text-only search",
                error=str(e),
            )
            self.embedding_model = None

    # ------------------------------------------------------------------
    # Simple fallback implementation
    # ------------------------------------------------------------------
    def _simple_path(self, business_id: int) -> Path:
        return self.simple_dir / f"business_{business_id}.json"

    def _load_simple_store(self, business_id: int) -> List[Dict[str, Any]]:
        path = self._simple_path(business_id)
        if not path.exists():
            return []
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.warning("Failed to read simple vector store", error=str(e))
            return []

    def _save_simple_store(self, business_id: int, data: List[Dict[str, Any]]) -> None:
        path = self._simple_path(business_id)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh)

    def _embed_texts(self, texts: List[str]) -> Optional[np.ndarray]:
        if not texts or not self.embedding_model:
            return None
        try:
            return np.asarray(self.embedding_model.encode(texts, show_progress_bar=False))
        except Exception as e:
            logger.warning("Embedding generation failed", error=str(e))
            return None

    # ------------------------------------------------------------------
    # Shared public API
    # ------------------------------------------------------------------
    def get_collection(self, business_id: int):
        if self.client is None:
            raise RuntimeError("Vector store client is not available")

        collection_name = f"business_{business_id}"

        try:
            collection = self.client.get_collection(name=collection_name)
            logger.debug(
                "Retrieved existing collection",
                business_id=business_id,
                collection=collection_name,
            )
        except Exception:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"business_id": business_id},
            )
            logger.info("Created new collection", business_id=business_id)

        return collection

    def add_documents(
        self,
        business_id: int,
        documents: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None,
    ) -> bool:

        texts = [doc.get("text", "") for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]
        ids = [doc.get("id", f"doc_{business_id}_{i}") for i, doc in enumerate(documents)]

        if self.mode == "chroma" and self.client is not None:
            return self._add_documents_chroma(business_id, texts, metadatas, ids, embeddings)

        return self._add_documents_simple(business_id, texts, metadatas, ids)

    def _add_documents_chroma(
        self,
        business_id: int,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        embeddings: Optional[List[List[float]]],
    ) -> bool:
        try:
            collection = self.get_collection(business_id)

            if self.embedding_model and not embeddings:
                embeddings_np = self._embed_texts(texts)
                embeddings = embeddings_np.tolist() if embeddings_np is not None else None

            preview_texts = [t[:200] for t in texts]
            logger.info(
                "Adding documents to collection",
                business_id=business_id,
                ids=ids,
                preview=preview_texts,
            )

            if embeddings:
                collection.add(
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids,
                )
            else:
                collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids,
                )

            return True

        except Exception as e:
            logger.error("Error adding documents to vector store", error=str(e))
            return False

    def _add_documents_simple(
        self,
        business_id: int,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> bool:

        logger.info("Using simple vector fallback", business_id=business_id)

        existing = self._load_simple_store(business_id)
        embeddings = self._embed_texts(texts)

        for idx, text in enumerate(texts):
            entry = {
                "id": ids[idx],
                "text": text,
                "metadata": metadatas[idx],
                "embedding": embeddings[idx].tolist() if embeddings is not None else None,
            }
            existing.append(entry)

        self._save_simple_store(business_id, existing)
        return True

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------
    def query_documents(
        self,
        business_id: int,
        query: str,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:

        if self.mode == "chroma" and self.client is not None:
            return self._query_chroma(business_id, query, n_results)

        return self._query_simple(business_id, query, n_results)

    def _query_chroma(self, business_id: int, query: str, n_results: int):
        try:
            collection = self.get_collection(business_id)

            query_embedding = None
            if self.embedding_model:
                q = self._embed_texts([query])
                if q is not None:
                    query_embedding = q.tolist()[0]

            if query_embedding:
                results = collection.query(
                    query_embeddings=[query_embedding], n_results=n_results
                )
            else:
                results = collection.query(query_texts=[query], n_results=n_results)

            documents = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            dists = results.get("distances", [[]])[0]

            for i, text in enumerate(docs):
                documents.append(
                    {
                        "text": text,
                        "metadata": metas[i] if metas else {},
                        "distance": dists[i] if dists else None,
                    }
                )

            return documents

        except Exception as e:
            logger.error("Error querying vector store", error=str(e))
            return []

    def _query_simple(self, business_id: int, query: str, n_results: int):
        entries = self._load_simple_store(business_id)
        if not entries:
            return []

        embeddings = np.array(
            [entry["embedding"] for entry in entries if entry.get("embedding")]
        )
        texts = [entry["text"] for entry in entries]
        metas = [entry.get("metadata", {}) for entry in entries]

        # Keyword search fallback
        if embeddings.size == 0 or not self.embedding_model:
            results = []
            query_lower = query.lower()
            for text, meta in zip(texts, metas):
                if query_lower in text.lower():
                    results.append({"text": text, "metadata": meta, "distance": None})
            return results[:n_results]

        query_embedding = self._embed_texts([query])
        if query_embedding is None:
            return []

        q = query_embedding[0]
        similarities = embeddings @ q / (
            np.linalg.norm(embeddings, axis=1) * np.linalg.norm(q) + 1e-10
        )

        top = np.argsort(similarities)[::-1][:n_results]

        return [
            {
                "text": texts[i],
                "metadata": metas[i],
                "distance": float(1 - similarities[i]),
            }
            for i in top
        ]

    # ------------------------------------------------------------------
    def delete_collection(self, business_id: int) -> bool:
        if self.mode == "chroma" and self.client is not None:
            try:
                self.client.delete_collection(name=f"business_{business_id}")
                return True
            except Exception as e:
                logger.error("Error deleting collection", error=str(e))
                return False

        path = self._simple_path(business_id)
        if path.exists():
            path.unlink()
        return True


# Global instance
vector_store = VectorStore()
