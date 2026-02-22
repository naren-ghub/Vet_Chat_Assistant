from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SessionState:
    session_id: str
    conversation_history: List[Tuple[str, str]] = field(default_factory=list)
    last_intent: Optional[str] = None
    pet_profile: Dict[str, Any] = field(default_factory=dict)
    severity_flag: bool = False
    retrieved_context: List[Dict[str, Any]] = field(default_factory=list)
    last_response_sources: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SearchResult:
    title: str
    link: str
    snippet: str
    source_domain: str


@dataclass
class RouteDecision:
    intent: str
    confidence: float
    route: str


@dataclass
class ChatResponse:
    text: str
    citations: List[Dict[str, Any]] = field(default_factory=list)
    emergency: bool = False
    map_link: Optional[str] = None
    follow_up_questions: List[str] = field(default_factory=list)
    vet_response: Optional[Dict[str, Any]] = None
