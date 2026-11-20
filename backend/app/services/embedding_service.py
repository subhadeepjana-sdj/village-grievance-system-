import logging
from typing import List
import numpy as np

logger = logging.getLogger("uvicorn.error")

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.dimension = 384
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer model '{self.model_name}'...")
            self.model = SentenceTransformer(self.model_name)
            if hasattr(self.model, "get_embedding_dimension"):
                self.dimension = self.model.get_embedding_dimension()
            else:
                self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"SentenceTransformer loaded successfully. Embedding dimension: {self.dimension}")
        except Exception as e:
            logger.warning(f"SentenceTransformer load skipped or failed ({e}). Using lightweight deterministic fallback vectorizer.")
            self.model = None

    def generate_embedding(self, text: str) -> List[float]:
        if self.model is not None:
            try:
                emb = self.model.encode(text, convert_to_numpy=True)
                return emb.tolist()
            except Exception as e:
                logger.error(f"Embedding generation error: {e}")

        # Deterministic lightweight fallback embedding (384-d normalized vector)
        return self._fallback_embedding(text)

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if self.model is not None:
            try:
                embs = self.model.encode(texts, convert_to_numpy=True)
                return embs.tolist()
            except Exception as e:
                logger.error(f"Batch embedding generation error: {e}")

        return [self._fallback_embedding(t) for t in texts]

    def _fallback_embedding(self, text: str) -> List[float]:
        # Hash-seeded deterministic pseudo-random embedding normalized to unit vector
        words = text.lower().split()
        vector = np.zeros(self.dimension, dtype=np.float32)
        for i, word in enumerate(words):
            val = sum(ord(c) for c in word)
            idx = (val * (i + 1)) % self.dimension
            vector[idx] += (val % 17) - 8.0
        
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        else:
            vector[0] = 1.0
        return vector.tolist()

embedding_service = EmbeddingService()
