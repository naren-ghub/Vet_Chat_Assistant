from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import requests

from core.errors import LLMError
from core.logging import get_logger


@dataclass
class GroqClient:
    api_key: str
    model: str
    temperature: float
    max_tokens: int
    top_p: float
    timeout_seconds: float = 30.0
    base_url: str = "https://api.groq.com/openai/v1"

    @property
    def model_name(self) -> str:
        return self.model

    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
    ) -> str:
        logger = get_logger("llm")
        last_exc: Exception | None = None

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature if temperature is None else temperature,
            "top_p": self.top_p if top_p is None else top_p,
            "max_tokens": self.max_tokens if max_tokens is None else max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(3):
            try:
                start = time.time()
                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )
                latency_ms = (time.time() - start) * 1000

                if resp.status_code >= 400:
                    raise LLMError(f"Groq API error ({resp.status_code})")

                data = resp.json()
                usage = data.get("usage") or {}
                logger.info(
                    "llm_latency_ms=%.1f prompt_tokens=%s output_tokens=%s total_tokens=%s",
                    latency_ms,
                    usage.get("prompt_tokens"),
                    usage.get("completion_tokens"),
                    usage.get("total_tokens"),
                )
                choices = data.get("choices") or []
                if not choices:
                    return ""
                msg = (choices[0].get("message") or {}).get("content")
                if not msg:
                    return ""
                return str(msg).strip()
            except Exception as exc:  # pragma: no cover - network failure
                last_exc = exc
                time.sleep(2**attempt)

        raise LLMError("LLM call failed after retries") from last_exc

