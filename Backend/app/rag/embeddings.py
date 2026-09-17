import math
import hashlib
import logging
from typing import List, Optional
from app.config.settings import get_settings

logger = logging.getLogger("ai_study_assistant.rag.embeddings")

EMBEDDING_DIMENSION = 768


class EmbeddingService:
    """
    Manages generation of dense text embeddings using Google's text-embedding-004 model
    with a deterministic normalized fallback for offline/local resilience.
    """

    def __init__(self):
        self.settings = get_settings()
        self._client = None
        self._init_client()

    def _init_client(self):
        if not self.settings.GEMINI_API_KEY:
            return
        try:
            from google import genai
            self._client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
        except Exception as e:
            logger.warning(f"Could not initialize GenAI client for embeddings: {e}")
            self._client = None

    def embed_text(self, text: str) -> List[float]:
        """Embeds a single string into a 768-dimensional float vector."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of texts into a list of 768-dimensional float vectors.
        Uses text-embedding-004 via the Google GenAI SDK if available,
        otherwise falls back to deterministic unit-normalized representation.
        """
        if not texts:
            return []

        if self._client:
            try:
                vectors: List[List[float]] = []
                # Process in batches of 16 to respect API limits
                batch_size = 16
                for i in range(0, len(texts), batch_size):
                    chunk_texts = texts[i:i + batch_size]
                    response = self._client.models.embed_content(
                        model="text-embedding-004",
                        contents=chunk_texts,
                    )
                    # Extract embeddings from response
                    if hasattr(response, "embeddings") and response.embeddings:
                        for emb in response.embeddings:
                            if hasattr(emb, "values"):
                                vectors.append(list(emb.values))
                            else:
                                vectors.append(list(emb))
                    elif hasattr(response, "embedding") and response.embedding:
                        if hasattr(response.embedding, "values"):
                            vectors.append(list(response.embedding.values))
                        else:
                            vectors.append(list(response.embedding))

                if len(vectors) == len(texts):
                    return vectors
            except Exception as e:
                logger.warning(f"Google GenAI embedding error: {e}. Utilizing deterministic fallback embeddings.")

        # Deterministic fallback
        return [self._generate_fallback_embedding(t) for t in texts]

    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """
        Generates a deterministic 768-dimensional unit-norm float vector from text.
        Combines character n-gram hashing to provide consistent semantic approximation
        when running in local offline development without API keys.
        """
        clean_text = text.lower().strip()
        vec = [0.0] * EMBEDDING_DIMENSION

        if not clean_text:
            return vec

        # Tokenize and hash n-grams
        tokens = clean_text.split()
        for token in tokens:
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % EMBEDDING_DIMENSION
            sign = 1.0 if ((h >> 8) & 1) else -1.0
            vec[idx] += sign * (1.0 + len(token) * 0.1)

        # Trigrams for sub-word matching
        for i in range(max(0, len(clean_text) - 2)):
            tri = clean_text[i:i + 3]
            h = int(hashlib.sha256(tri.encode("utf-8")).hexdigest()[:8], 16)
            idx = h % EMBEDDING_DIMENSION
            sign = 1.0 if ((h >> 4) & 1) else -1.0
            vec[idx] += sign * 0.5

        # Normalize to unit length
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [round(x / norm, 6) for x in vec]

        return vec

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Calculates cosine similarity between two float vectors."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return float(dot / (norm_a * norm_b))


_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
