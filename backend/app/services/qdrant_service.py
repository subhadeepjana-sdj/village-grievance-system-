import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest_models
from app.config import settings

logger = logging.getLogger("uvicorn.error")


class QdrantService:
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION
        self.client = self._init_client()
        self._ensure_collection()

    def _init_client(self) -> QdrantClient:
        try:
            client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=3.0)
            client.get_collections()
            logger.info("Connected to remote Qdrant server successfully.")
            return client
        except Exception as e:
            logger.warning(
                f"Could not connect to Qdrant server at {settings.QDRANT_HOST}:{settings.QDRANT_PORT} "
                f"({e}). Using in-memory Qdrant instance."
            )
            return QdrantClient(":memory:")

    def _ensure_collection(self):
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if self.collection_name not in collections:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=rest_models.VectorParams(
                        size=384,
                        distance=rest_models.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection '{self.collection_name}'.")
        except Exception as e:
            logger.error(f"Failed to ensure Qdrant collection: {e}")

    # ------------------------------------------------------------------ #
    #  Write operations                                                    #
    # ------------------------------------------------------------------ #

    def upsert_chunks(self, points: List[Dict[str, Any]]):
        if not points:
            return
        qdrant_points = [
            rest_models.PointStruct(
                id=p["id"],
                vector=p["vector"],
                payload=p["payload"]
            )
            for p in points
        ]
        self.client.upsert(collection_name=self.collection_name, points=qdrant_points)
        logger.info(f"Upserted {len(points)} chunks into Qdrant collection '{self.collection_name}'.")

    def delete_document_chunks(self, document_id: int) -> None:
        """
        Delete all Qdrant points that belong to *document_id*.

        Uses a payload filter on the ``document_id`` field — the same field
        written by DocumentParserService.process_and_index_document().
        Safe to call when no chunks exist for the given document.
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=rest_models.FilterSelector(
                    filter=rest_models.Filter(
                        must=[
                            rest_models.FieldCondition(
                                key="document_id",
                                match=rest_models.MatchValue(value=document_id)
                            )
                        ]
                    )
                )
            )
            logger.info(f"Deleted Qdrant chunks for document_id={document_id}")
        except Exception as e:
            logger.error(f"Failed to delete Qdrant chunks for document_id={document_id}: {e}")

    # ------------------------------------------------------------------ #
    #  Read operations                                                     #
    # ------------------------------------------------------------------ #

    def search_similar(
        self,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: float = 0.2
    ) -> List[Dict[str, Any]]:
        """Unfiltered semantic search — kept for backward compatibility."""
        return self.search_similar_filtered(query_vector, top_k, score_threshold)

    def search_similar_filtered(
        self,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: float = 0.2,
        department_filter: Optional[str] = None,
        verified_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Semantic search with optional metadata filters.

        Parameters
        ----------
        query_vector:      Dense embedding of the user query.
        top_k:             Maximum results to return.
        score_threshold:   Minimum cosine similarity to include.
        department_filter: If set, only return chunks whose ``department``
                           payload field exactly matches this value.
        verified_only:     If True (default), only return chunks whose
                           ``status`` payload field is ``"verified"``.
                           Set False to include pending/expired docs (admin use).
        """
        must_conditions = []

        if verified_only:
            must_conditions.append(
                rest_models.FieldCondition(
                    key="status",
                    match=rest_models.MatchValue(value="verified")
                )
            )

        if department_filter:
            must_conditions.append(
                rest_models.FieldCondition(
                    key="department",
                    match=rest_models.MatchValue(value=department_filter)
                )
            )

        filter_obj = rest_models.Filter(must=must_conditions) if must_conditions else None

        hits: List[Dict[str, Any]] = []
        try:
            # Newer qdrant-client exposes query_points(); older versions use search()
            if hasattr(self.client, "query_points"):
                res = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    limit=top_k,
                    score_threshold=score_threshold,
                    query_filter=filter_obj
                )
                points = getattr(res, "points", res)
                for pt in points:
                    hits.append({
                        "id": pt.id,
                        "score": float(pt.score),
                        "payload": pt.payload
                    })
            elif hasattr(self.client, "search"):
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=top_k,
                    score_threshold=score_threshold,
                    query_filter=filter_obj
                )
                for res in results:
                    hits.append({
                        "id": res.id,
                        "score": float(res.score),
                        "payload": res.payload
                    })
        except Exception as e:
            logger.error(f"Qdrant similarity search error: {e}")

        return hits


qdrant_service = QdrantService()
