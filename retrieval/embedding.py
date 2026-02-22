from __future__ import annotations

from typing import List


_MODEL_CACHE = {}


def get_embedding_model(model_name: str):
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


class BGEEmbedder:
    def __init__(self, model_name: str) -> None:
        self._model = get_embedding_model(model_name)

    def encode(self, texts: List[str]):
        return self._model.encode(texts, normalize_embeddings=True)
