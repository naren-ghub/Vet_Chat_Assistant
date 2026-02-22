from __future__ import annotations


class VetChatError(Exception):
    """Base error for vet chat system."""


class VectorDBError(VetChatError):
    """Vector DB unavailable or query failure."""


class LLMError(VetChatError):
    """LLM invocation failed."""


class LiveSearchError(VetChatError):
    """Live search provider failure."""


class ValidationError(VetChatError):
    """Structured validation failure."""
