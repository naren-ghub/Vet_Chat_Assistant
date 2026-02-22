from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ValidationError


class Citation(BaseModel):
    source_title: str
    organization: str
    publication_year: Optional[int] = None
    section_reference: Optional[str] = None
    url: Optional[str] = None


class VetResponse(BaseModel):
    answer: str
    possible_causes: str
    warning_signs: str
    vet_visit_guidance: str
    care_tips: Optional[str] = None
    citations: List[Citation] = []


def validate_kb_citations(
    citations: List[dict],
    allowed_source_titles: List[str],
    min_similarity: float,
) -> List[Citation]:
    allowed = {title.strip().lower() for title in allowed_source_titles if title}
    validated: List[Citation] = []
    for item in citations:
        similarity = item.get("similarity_score")
        if similarity is not None and similarity < min_similarity:
            continue
        try:
            citation = Citation.model_validate(item)
        except ValidationError:
            continue
        if citation.source_title.strip().lower() not in allowed:
            continue
        validated.append(citation)
    return validated


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    snippet = text[start : end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        return None


def parse_vet_response(text: str) -> Optional[VetResponse]:
    payload = _extract_json(text)
    if not payload:
        return None
    try:
        return VetResponse.model_validate(payload)
    except ValidationError:
        return None


def fallback_vet_response() -> VetResponse:
    return VetResponse(
        answer="I’m not fully confident in the available information.",
        possible_causes="There may be several possible causes.",
        warning_signs="If symptoms worsen or severe signs appear, seek urgent care.",
        vet_visit_guidance="Please consult a licensed veterinarian.",
        care_tips="Keep your pet comfortable and monitor closely.",
        citations=[],
    )


def format_vet_response(response: VetResponse) -> str:
    lines = [
        f"Answer: {response.answer}",
        f"Possible Causes: {response.possible_causes}",
        f"Warning Signs: {response.warning_signs}",
        f"When to See a Vet: {response.vet_visit_guidance}",
    ]
    if response.care_tips:
        lines.append(f"Care Tips: {response.care_tips}")
    return "\n".join(lines)
