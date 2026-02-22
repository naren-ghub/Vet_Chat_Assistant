from __future__ import annotations

from typing import List

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


def generate_questions(llm, user_input: str, missing_fields: List[str], suspected_intent: str) -> List[str]:
    prompt = compose_prompt(
        "prompts/question_prompt.txt",
        user_input=user_input,
        missing_fields=", ".join(missing_fields),
        suspected_intent=suspected_intent,
    )
    text = llm.generate(prompt)
    questions = []
    for line in text.splitlines():
        line = line.strip().lstrip("-•").strip()
        if line:
            questions.append(line)
    return questions[:4]
