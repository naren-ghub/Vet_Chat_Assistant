from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable


@dataclass(frozen=True)
class LLMConfig:
    temperature: float
    max_tokens: int
    top_p: float
    structured_validation_required: bool


@runtime_checkable
class LLMClient(Protocol):
    model_name: str

    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
    ) -> str: ...

