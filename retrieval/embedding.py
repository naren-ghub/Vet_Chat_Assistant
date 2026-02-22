from __future__ import annotations

from typing import List


class BGEEmbedder:
    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as exc:  # pragma: no cover - import guard
            raise RuntimeError(
                "Missing dependency: sentence-transformers. "
                "Install with `pip install sentence-transformers`."
            ) from exc
        self._model = SentenceTransformer(model_name)

    def encode(self, texts: List[str]):
        return self._model.encode(texts, normalize_embeddings=True)
