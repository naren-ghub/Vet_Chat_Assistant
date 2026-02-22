from __future__ import annotations

import re


DOSAGE_PATTERN = re.compile(r"\b(\d+(\.\d+)?\s*(mg|ml|mcg|g|iu)\b|\bmg/kg\b|\bml/kg\b)", re.I)


def apply_safety_guardrails(text: str) -> str:
    if DOSAGE_PATTERN.search(text):
        text += (
            "\n\nSafety note: I cannot provide medication dosages. "
            "Please contact a licensed veterinarian for dosing guidance."
        )
    if "definitive diagnosis" in text.lower():
        text = text.replace("definitive diagnosis", "suggested possibility")
    return text
