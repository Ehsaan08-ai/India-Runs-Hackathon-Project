import os
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List

# Lazy singleton
_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        # Use a solid small model — local, free, fast
        model_name = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
        _model = SentenceTransformer(model_name)
    return _model

def embed_text(text: str) -> np.ndarray:
    model = get_model()
    return model.encode(text, normalize_embeddings=True)

def embed_texts(texts: List[str]) -> np.ndarray:
    model = get_model()
    return model.encode(texts, normalize_embeddings=True, batch_size=32)

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))

def candidate_to_text(candidate: dict) -> str:
    """Flatten a candidate dict into a single semantic-search-friendly string."""
    parts = []
    for key, value in candidate.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            value = ", ".join(str(v) for v in value)
        elif isinstance(value, dict):
            value = ", ".join(f"{k}: {v}" for k, v in value.items())
        parts.append(f"{key.replace('_', ' ')}: {value}")
    return "\n".join(parts)