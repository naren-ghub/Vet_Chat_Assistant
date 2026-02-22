from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from core.chat import chat
from core.config import load_config
from core.response import VetResponse
from core.session_store import SessionStore
from core.errors import VetChatError
from core.llm import GeminiClient
from retrieval.embedding import BGEEmbedder
from retrieval.vector_store import get_collection


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    pet_profile: Optional[Dict[str, Any]] = None


class ChatResponseModel(BaseModel):
    text: str
    citations: List[Dict[str, Any]] = []
    emergency: bool = False
    map_link: Optional[str] = None
    follow_up_questions: List[str] = []
    vet_response: Optional[VetResponse] = None


class LocationRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)


class HealthResponse(BaseModel):
    status: str = "ok"


app = FastAPI(title="Vet Chat Assistant", version="1.0")
_config = load_config()
_store = SessionStore(ttl_seconds=1800)


@app.post("/chat", response_model=ChatResponseModel)
def chat_endpoint(payload: ChatRequest) -> ChatResponseModel:
    session = _store.get(payload.session_id)
    if payload.pet_profile:
        session.pet_profile.update(payload.pet_profile)
    llm = GeminiClient(
        _config.gemini_api_key,
        _config.gemini_model,
        _config.llm_temperature,
        _config.llm_max_tokens,
        _config.llm_top_p,
        _config.llm_timeout_seconds,
    )
    embedder = BGEEmbedder(_config.bge_model)
    collection = get_collection(_config.chroma_path)
    try:
        response = chat(
            payload.message,
            session,
            _config,
            llm_client=llm,
            embedder=embedder,
            collection=collection,
        )
    except VetChatError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    data = response.__dict__.copy()
    if data.get("vet_response"):
        data["vet_response"] = VetResponse.model_validate(data["vet_response"])
    return ChatResponseModel(**data)


@app.post("/location")
def location_endpoint(payload: LocationRequest) -> Dict[str, str]:
    _store.update_location(payload.session_id, payload.location)
    return {"status": "ok"}


@app.get("/health", response_model=HealthResponse)
def health_endpoint() -> HealthResponse:
    return HealthResponse()
