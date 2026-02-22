from __future__ import annotations

import os
from typing import List


_MODEL_CACHE = {}


def get_embedding_model(model_name: str):
    if os.getenv("TEST_MODE") == "1":
        return DummyEmbedder()
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as exc:  # pragma: no cover - import guard
        raise RuntimeError(
            "Missing dependency: sentence-transformers. "
            "Install with `pip install sentence-transformers`."
        ) from exc
    if model_name not in _MODEL_CACHE:
        _MODEL_CACHE[model_name] = SentenceTransformer(model_name)
    return _MODEL_CACHE[model_name]


class DummyEmbedder:
    def encode(self, texts, **kwargs):
        return [[0.1] * 8 for _ in texts]


class BGEEmbedder:
    def __init__(self, model_name: str) -> None:
        self._model = get_embedding_model(model_name)

    def encode(self, texts: List[str]):
        return self._model.encode(texts, normalize_embeddings=True)
