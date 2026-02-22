from __future__ import annotations

from core.intent import (
    emergency_score,
    rule_based_intent,
    embedding_similarity_intent,
    llm_intent,
    INTENT_EXEMPLARS,
)
from core.types import RouteDecision


def route_intent(
    text: str,
    embedder,
    llm,
    emergency_threshold: float,
    high_threshold: float,
    medium_threshold: float,
) -> RouteDecision:
    label, confidence = rule_based_intent(text)
    if label:
        route = label
        return RouteDecision(intent=label, confidence=confidence, route=route)

    if emergency_score(text) >= emergency_threshold:
        return RouteDecision(intent="emergency", confidence=0.9, route="emergency")

    label, confidence = embedding_similarity_intent(text, embedder, INTENT_EXEMPLARS)
    if confidence < medium_threshold:
        label = llm_intent(text, llm)
        return RouteDecision(intent=label, confidence=0.5, route=label)

    route = "medical_query"
    if label == "emergency":
        route = "emergency"
    elif label == "clinic_search":
        route = "clinic_search"
    elif label == "vaccination":
        route = "medical_query"

    return RouteDecision(intent=label, confidence=confidence, route=route)
