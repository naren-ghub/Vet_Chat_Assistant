from __future__ import annotations

import time
from typing import Any, Dict, Optional

from core.errors import LLMError
from core.logging import get_logger


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        timeout_seconds: float,
    ) -> None:
        try:
            from google import genai
            from google.genai import types
        except Exception as exc:  # pragma: no cover - import guard
            raise RuntimeError(
                "Missing dependency: google-genai. "
                "Install with `pip install google-genai`."
            ) from exc
        self._types = types
        self._client = genai.Client(api_key=api_key)
        self._model_name = model
        self._temperature = temperature
        self._top_p = top_p
        self._max_tokens = max_tokens
        self._generation_config = types.GenerateContentConfig(
            temperature=self._temperature,
            top_p=self._top_p,
            max_output_tokens=self._max_tokens,
        )

    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
    ) -> str:
        logger = get_logger("llm")
        last_exc = None
        config = self._generation_config

        if temperature is not None or max_tokens is not None or top_p is not None:
            config = self._types.GenerateContentConfig(
                temperature=self._temperature if temperature is None else temperature,
                top_p=self._top_p if top_p is None else top_p,
                max_output_tokens=self._max_tokens if max_tokens is None else max_tokens,
            )

        for attempt in range(3):
            try:
                start = time.time()
                response = self._client.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                    config=config,
                )

                latency_ms = (time.time() - start) * 1000
                usage = getattr(response, "usage_metadata", None)

                if usage:
                    logger.info(
                        "llm_latency_ms=%.1f prompt_tokens=%s output_tokens=%s total_tokens=%s",
                        latency_ms,
                        getattr(usage, "prompt_token_count", None),
                        getattr(usage, "candidates_token_count", None),
                        getattr(usage, "total_token_count", None),
                    )
                else:
                    logger.info("llm_latency_ms=%.1f", latency_ms)

                text = getattr(response, "text", None)
                if not text:
                    return ""

                return text.strip()

            except Exception as exc:  # pragma: no cover - network failure
                last_exc = exc
                time.sleep(2 ** attempt)

        raise LLMError("LLM call failed after retries") from last_exc
