from __future__ import annotations

from core.config import AppConfig
from core.llm_base import LLMClient


def build_llm_client(config: AppConfig) -> LLMClient:
    # Provider-specific implementation lives here to keep core orchestration provider-agnostic.
    from core.llm_groq import GroqClient

    return GroqClient(
        api_key=config.groq_api_key,
        model=config.groq_model,
        temperature=config.llm_temperature,
        max_tokens=config.llm_max_tokens,
        top_p=config.llm_top_p,
        timeout_seconds=config.llm_timeout_seconds,
    )
