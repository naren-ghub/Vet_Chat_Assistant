from __future__ import annotations

from core.config import AppConfig
from core.llm_base import LLMConfig


def select_llm_config(query_context: str, response_style: str, config: AppConfig) -> LLMConfig:
    """
    Controlled autonomy policy (Architecture Update - 4).

    - CLINICAL_SPECIFIC: strict, low-temp, structured validation required
    - ACADEMIC: higher temp, longer responses, no structured schema requirement
    - GENERAL: moderate temp, longer responses, no structured schema requirement
    """
    qc = (query_context or "GENERAL").upper()
    style = (response_style or "clinical").lower()

    if qc == "CLINICAL_SPECIFIC" or style == "clinical":
        return LLMConfig(
            temperature=float(config.llm_temperature),
            max_tokens=int(config.llm_max_tokens),
            top_p=float(config.llm_top_p),
            structured_validation_required=True,
        )

    if qc == "ACADEMIC":
        return LLMConfig(
            temperature=0.4,
            max_tokens=700,
            top_p=float(config.llm_top_p),
            structured_validation_required=False,
        )

    return LLMConfig(
        temperature=0.35,
        max_tokens=600,
        top_p=float(config.llm_top_p),
        structured_validation_required=False,
    )

