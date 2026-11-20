import logging
from typing import List, Dict, Any
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
            logger.warning(f"Could not connect to Qdrant server at {settings.QDRANT_HOST}:{settings.QDRANT_PORT} ({e}). Using in-memory Qdrant instance.")
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

    def search_similar(self, query_vector: List[float], top_k: int = 5, score_threshold: float = 0.2) -> List[Dict[str, Any]]:
        hits = []
        try:
            # Check for newer qdrant-client query_points API vs search API
            if hasattr(self.client, "query_points"):
                res = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    limit=top_k,
                    score_threshold=score_threshold
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
                    score_threshold=score_threshold
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
