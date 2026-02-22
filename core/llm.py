from __future__ import annotations

from typing import Any, Dict, Optional


class GeminiClient:
    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int, top_p: float) -> None:
        try:
            import google.generativeai as genai
        except Exception as exc:  # pragma: no cover - import guard
            raise RuntimeError(
                "Missing dependency: google-generativeai. "
                "Install with `pip install google-generativeai`."
            ) from exc
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)
        self._generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "top_p": top_p,
        }

    def generate(self, prompt: str) -> str:
        import time

from core.logging import get_logger
from core.errors import LLMError

        logger = get_logger("llm")
        last_exc = None
        for attempt in range(3):
            try:
                start = time.time()
                response = self._model.generate_content(
                    prompt, generation_config=self._generation_config
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
