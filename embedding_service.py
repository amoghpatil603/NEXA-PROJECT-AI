from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance.model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        return cls._instance

    def embed_text(self, text: str) -> np.ndarray:
        return self.model.encode(text)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(texts)

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
