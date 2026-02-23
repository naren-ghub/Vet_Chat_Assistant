from __future__ import annotations

from typing import List, Tuple, Optional

import json

from core.prompts import compose_prompt
from core.logging import get_logger
from core.llm_base import LLMConfig, LLMClient


def detect_missing_fields(text: str, pet_profile: dict) -> List[str]:
    missing = []
    lowered = text.lower()
    if "dog" not in lowered and "cat" not in lowered and "species" not in pet_profile:
        missing.append("species")
    if "age" not in lowered and "age" not in pet_profile:
        missing.append("age")
    if "how long" not in lowered and "duration" not in pet_profile:
        missing.append("duration")
    return missing


def generate_questions(
    llm: LLMClient,
    user_input: str,
    missing_fields: List[str],
    suspected_intent: str,
    llm_config: Optional[LLMConfig] = None,
    log_meta: Optional[dict] = None,
) -> Tuple[str, List[str]]:
    prompt = compose_prompt(
        "prompts/question_prompt.txt",
        user_input=user_input,
        missing_fields=", ".join(missing_fields),
        suspected_intent=suspected_intent,
    )
    if log_meta:
        get_logger("vet-chat").info(
            "llm_call model=%s query_context=%s response_style=%s response_mode=%s temperature=%s max_tokens=%s top_p=%s",
            getattr(llm, "model_name", "unknown"),
            log_meta.get("query_context"),
            log_meta.get("response_style"),
            log_meta.get("response_mode"),
            getattr(llm_config, "temperature", None),
            getattr(llm_config, "max_tokens", None),
            getattr(llm_config, "top_p", None),
        )

    temperature = llm_config.temperature if llm_config else None
    max_tokens = llm_config.max_tokens if llm_config else None
    top_p = llm_config.top_p if llm_config else None
    text = llm.generate(prompt, temperature=temperature, max_tokens=max_tokens, top_p=top_p)
    guidance = ""
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            payload = json.loads(stripped)
            guidance = (payload.get("guidance") or "").strip()
            questions = [q.strip() for q in payload.get("questions") or [] if q.strip()]
            return guidance, questions[:4]
        except json.JSONDecodeError:
            pass
    questions = []
    for line in text.splitlines():
        line = line.strip().lstrip("-•").strip()
        if line:
            questions.append(line)
    return guidance, questions[:4]
