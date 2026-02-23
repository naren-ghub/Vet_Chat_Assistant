from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

from core.errors import ConfigurationError

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional
    load_dotenv = None


@dataclass
class AppConfig:
    groq_api_key: str
    groq_model: str
    llm_temperature: float
    llm_max_tokens: int
    llm_top_p: float
    llm_timeout_seconds: float
    bge_model: str
    chroma_path: str
    serper_api_key: str
    serper_endpoint: str
    domain_allowlist_path: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    retrieval_confidence_threshold: float
    intent_high_threshold: float
    intent_medium_threshold: float
    emergency_threshold: float
    live_search_enabled: bool


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise ConfigurationError(f"Missing required environment variable: {name}")
    return value


def load_config() -> AppConfig:
    if load_dotenv:
        load_dotenv()
    groq_api_key = _env("GROQ_API_KEY")

    return AppConfig(
        groq_api_key=groq_api_key,
        groq_model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", "512")),
        llm_top_p=float(os.getenv("LLM_TOP_P", "0.9")),
        llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
        bge_model=os.getenv("BGE_MODEL", "BAAI/bge-base-en-v1.5"),
        chroma_path=os.getenv("CHROMA_PATH", "data/chroma"),
        serper_api_key=_env("SERPER_API_KEY"),
        serper_endpoint=os.getenv(
            "SERPER_ENDPOINT", "https://google.serper.dev/search"
        ),
        domain_allowlist_path=os.getenv("DOMAIN_ALLOWLIST_PATH", "domain.txt"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "800")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "160")),
        top_k=int(os.getenv("TOP_K", "5")),
        retrieval_confidence_threshold=float(
            os.getenv("RETRIEVAL_CONFIDENCE_THRESHOLD", "0.62")
        ),
        intent_high_threshold=float(os.getenv("INTENT_HIGH_THRESHOLD", "0.82")),
        intent_medium_threshold=float(os.getenv("INTENT_MEDIUM_THRESHOLD", "0.65")),
        emergency_threshold=float(os.getenv("EMERGENCY_THRESHOLD", "8.0")),
        live_search_enabled=os.getenv("LIVE_SEARCH_ENABLED", "true").lower() == "true",
    )


def load_domain_allowlist(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as handle:
        domains = [line.strip().lower() for line in handle if line.strip()]
    return domains
