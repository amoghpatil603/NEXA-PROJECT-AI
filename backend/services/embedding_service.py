import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    HAS_ST = True
except Exception:
    HAS_ST = False

class EmbeddingService:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            if HAS_ST:
                try:
                    cls._instance.model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
                except Exception:
                    cls._instance.model = None
            else:
                cls._instance.model = None
        return cls._instance

    def embed_text(self, text: str) -> np.ndarray:
        if hasattr(self, 'model') and self.model is not None:
            try:
                return self.model.encode(text)
            except Exception:
                pass

        vec = np.zeros(384, dtype=np.float32)
        words = str(text).lower().split()
        for w in words:
            idx = abs(hash(w)) % 384
            vec[idx] += 1.0
            for i in range(len(w) - 2):
                ngram = w[i:i+3]
                ngram_idx = abs(hash(ngram)) % 384
                vec[ngram_idx] += 0.5

        norm = np.linalg.norm(vec)
        if norm > 0:
            return vec / norm
        else:
            return np.ones(384, dtype=np.float32) / np.sqrt(384)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        return np.array([self.embed_text(t) for t in texts])

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot_product / (norm1 * norm2))
