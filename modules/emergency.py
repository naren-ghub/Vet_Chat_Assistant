from __future__ import annotations

from core.intent import emergency_score, has_immediate_override


def is_emergency(text: str, threshold: float) -> bool:
    if has_immediate_override(text):
        return True
    return emergency_score(text) >= threshold
