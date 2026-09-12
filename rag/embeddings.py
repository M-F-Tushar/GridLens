from __future__ import annotations

import hashlib
import math
import re

EMBEDDING_DIM = 256
_TOKEN_RE = re.compile(r"[a-z0-9]+")

_STOPWORDS = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
        "have", "in", "is", "it", "its", "of", "on", "or", "that", "the",
        "this", "to", "was", "were", "will", "with", "not", "no",
    }
)

def tokenize(text: str) -> list[str]:
    tokens = _TOKEN_RE.findall(text.lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


def _stable_bucket(token: str, dim: int) -> int:
    """
    Deterministically map a single token string to an integer bucket 
    index in [0, dim), functioning like the hashing trick in 
    scikit-learn's HashingVectorizer.
    """
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % dim


def embed_text(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """
    The core function — converts an arbitrary string into a deterministic, 
    fixed-length, L2-normalized "bag-of-words hashing" embedding vector.
    """
    vector = [0.0] * dim
    tokens = tokenize(text)
    if not tokens:
        return vector
    for token in tokens:
        bucket = _stable_bucket(token, dim)
        vector[bucket] += 1.0

    norm = math.sqrt(sum(v * v for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]
    return vector


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    Compute the cosine similarity between two embedding vectors — 
    the core relevance-scoring metric used by VectorStore.search().
    """
    if len(a) != len(b):
        raise ValueError("Vectors must have the same dimensionality")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)