from __future__ import annotations

from typing import List, Tuple

import json

from core.prompts import compose_prompt


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
    llm, user_input: str, missing_fields: List[str], suspected_intent: str
) -> Tuple[str, List[str]]:
    prompt = compose_prompt(
        "prompts/question_prompt.txt",
        user_input=user_input,
        missing_fields=", ".join(missing_fields),
        suspected_intent=suspected_intent,
    )
    text = llm.generate(prompt)
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
