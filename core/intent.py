from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from core.llm import GeminiClient
from core.prompts import compose_prompt
import numpy as np


INTENT_EXEMPLARS: Dict[str, List[str]] = {
    "emergency": [
        "my dog is collapsing",
        "seizure and not breathing",
        "poisoned cat",
    ],
    "clinic_search": [
        "find a vet near me",
        "nearest animal hospital",
        "vet clinic nearby",
    ],
    "medical_query": [
        "my dog is vomiting",
        "cat has diarrhea",
        "symptoms of rabies",
    ],
    "vaccination": [
        "vaccination schedule for dogs",
        "rabies shot timing",
    ],
    "general_info": [
        "what is parvovirus",
        "what is zoonotic disease",
    ],
}


EMERGENCY_KEYWORDS = {
    "seizure": 4.0,
    "poison": 4.0,
    "collapse": 3.0,
    "uncontrolled bleeding": 4.0,
    "difficulty breathing": 4.5,
    "not breathing": 5.0,
}

IMMEDIATE_OVERRIDE = {
    "difficulty breathing",
    "not breathing",
    "seizure",
    "collapse",
    "poison",
}


def rule_based_intent(text: str) -> Tuple[str | None, float]:
    lowered = text.lower()
    if any(k in lowered for k in ["nearest vet", "vet near", "animal hospital", "clinic"]):
        return "clinic_search", 0.85
    if any(k in lowered for k in ["vaccine", "vaccination", "rabies shot"]):
        return "vaccination", 0.8
    if any(k in lowered for k in EMERGENCY_KEYWORDS):
        return "emergency", 0.9
    return None, 0.0


def emergency_score(text: str) -> float:
    lowered = text.lower()
    score = 0.0
    for keyword, weight in EMERGENCY_KEYWORDS.items():
        if keyword in lowered:
            score += weight
    if "hours" in lowered or "days" in lowered:
        score += 1.0
    return score


def has_immediate_override(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in IMMEDIATE_OVERRIDE)


def embedding_similarity_intent(
    text: str, embedder, exemplars: Dict[str, List[str]]
) -> Tuple[str, float]:
    query_vec = embedder.encode([text])[0]
    best_intent = "medical_query"
    best_score = -1.0
    for intent, samples in exemplars.items():
        sample_vecs = embedder.encode(samples)
        for vec in sample_vecs:
            denom = (np.linalg.norm(query_vec) * np.linalg.norm(vec)) + 1e-9
            score = float((query_vec @ vec) / denom)
            if score > best_score:
                best_score = score
                best_intent = intent
    return best_intent, min(max(best_score, 0.0), 1.0)


def llm_intent(text: str, llm: GeminiClient) -> str:
    prompt = compose_prompt("prompts/intent_prompt.txt", message=text)
    label = llm.generate(prompt).strip().lower()
    for allowed in [
        "emergency",
        "clinic_search",
        "medical_query",
        "vaccination",
        "general_info",
        "missing_info",
    ]:
        if allowed == label:
            return label
    return "medical_query"
