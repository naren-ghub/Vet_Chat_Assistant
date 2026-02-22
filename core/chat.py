from __future__ import annotations

from typing import List

import json

from core.cache import TTLCache
from core.config import AppConfig, load_domain_allowlist
from core.errors import LiveSearchError, VectorDBError
from core.llm import GeminiClient
from core.logging import get_logger
from core.prompts import compose_prompt
from core.response import (
    VetResponse,
    fallback_vet_response,
    format_vet_response,
    parse_vet_response,
    validate_kb_citations,
)
from core.router import route_intent
from core.safety import apply_safety_guardrails
from core.types import ChatResponse, SessionState
from modules.emergency import is_emergency
from modules.live_search import live_search
from modules.map_locator import build_map_link
from modules.question_engine import detect_missing_fields, generate_questions
from modules.rag import rag_context
from retrieval.embedding import BGEEmbedder
from retrieval.vector_store import get_collection, query_collection


_embedding_cache = TTLCache(ttl_seconds=3600)
_retrieval_cache = TTLCache(ttl_seconds=3600)
_response_cache = TTLCache(ttl_seconds=3600)
_llm_cache = TTLCache(ttl_seconds=3600)
_logger = get_logger("vet-chat")


def _build_filter_key(session: SessionState) -> str:
    filter_payload = {
        "species": session.pet_profile.get("species"),
        "severity": session.pet_profile.get("severity"),
    }
    return json.dumps(filter_payload, sort_keys=True)


def build_where_filters(session: SessionState, route) -> dict | None:
    filters = {}
    species = session.pet_profile.get("species")
    if species:
        filters["$or"] = [{"species": species}, {"species": "all"}]
    if route.intent == "vaccination":
        filters["category"] = "vaccination"
    return filters if filters else None


def _build_retrieval_key(query: str, config: AppConfig, session: SessionState) -> str:
    filter_key = _build_filter_key(session)
    return (
        f"{query.lower()}|{config.top_k}|{config.bge_model}|"
        f"{config.retrieval_confidence_threshold}|{filter_key}"
    )


def _use_live_search(text: str, confidence: float, threshold: float) -> bool:
    if "latest" in text.lower() or "recent" in text.lower():
        return True
    return confidence < threshold


def _format_live_search_results(results) -> str:
    if not results:
        return ""
    lines = ["Live search summary:"]
    for r in results[:5]:
        lines.append(f"- {r.title} ({r.source_domain}): {r.snippet}")
    return "\n".join(lines)


def _llm_generate(llm: GeminiClient, prompt: str) -> str:
    cached = _llm_cache.get(prompt)
    if cached:
        return cached
    text = llm.generate(prompt)
    _llm_cache.set(prompt, text)
    return text


def _embed_query(embedder: BGEEmbedder, query: str):
    cached = _embedding_cache.get(query)
    if cached is not None:
        return cached
    vec = embedder.encode([query])[0]
    _embedding_cache.set(query, vec)
    return vec


def _validate_llm_response(prompt: str, llm: GeminiClient) -> VetResponse:
    text = _llm_generate(llm, prompt)
    parsed = parse_vet_response(text)
    if parsed:
        return parsed
    retry_prompt = prompt + "\n\nReturn ONLY valid JSON that matches the schema."
    text = _llm_generate(llm, retry_prompt)
    parsed = parse_vet_response(text)
    if parsed:
        return parsed
    return fallback_vet_response()


def chat(query: str, session: SessionState, config: AppConfig) -> ChatResponse:
    llm = GeminiClient(
        config.gemini_api_key,
        config.gemini_model,
        config.llm_temperature,
        config.llm_max_tokens,
        config.llm_top_p,
    )
    embedder = BGEEmbedder(config.bge_model)
    try:
        collection = get_collection(config.chroma_path)
    except Exception as exc:
        raise VectorDBError("Vector DB unavailable") from exc

    route = route_intent(
        query,
        embedder,
        llm,
        config.emergency_threshold,
        config.intent_high_threshold,
        config.intent_medium_threshold,
    )
    from core.intent import emergency_score
    _logger.info("emergency_score=%.2f", emergency_score(query))
    session.last_intent = route.intent
    _logger.info("intent=%s confidence=%.2f route=%s", route.intent, route.confidence, route.route)

    if route.route == "clinic_search":
        link = build_map_link("veterinary clinic")
        return ChatResponse(
            text="Here is a nearby veterinary clinic search link.",
            map_link=link,
        )

    if route.route == "emergency" or is_emergency(query, config.emergency_threshold):
        prompt = compose_prompt("prompts/emergency_prompt.txt", question=query)
        vet_response = _validate_llm_response(prompt, llm)
        vet_response.citations = []
        answer = format_vet_response(vet_response)
        answer = apply_safety_guardrails(answer)
        return ChatResponse(
            text=answer,
            emergency=True,
            vet_response=vet_response.model_dump(),
        )

    missing = detect_missing_fields(query, session.pet_profile)
    if missing:
        questions = generate_questions(llm, query, missing, route.intent)
        return ChatResponse(
            text="I need a few details to help.",
            follow_up_questions=questions,
        )

    profile_key = json.dumps(session.pet_profile, sort_keys=True, default=str)
    response_key = f"{query.lower()}|{profile_key}|{session.last_intent or ''}"
    cached_response = _response_cache.get(response_key)
    if cached_response:
        return cached_response

    query_embedding = _embed_query(embedder, query)
    where_filters = build_where_filters(session, route)
    retrieval_key = _build_retrieval_key(query, config, session)
    cached_retrieval = _retrieval_cache.get(retrieval_key)
    if cached_retrieval:
        rag_text, citations, allowed_titles, retrieval = cached_retrieval
    else:
        rag_text, citations, allowed_titles = rag_context(
            collection,
            query_embedding,
            config.top_k,
            where=where_filters,
        )
        retrieval = query_collection(
            collection, query_embedding, top_k=config.top_k, where=where_filters
        )
        _retrieval_cache.set(retrieval_key, (rag_text, citations, allowed_titles, retrieval))

    # Compute retrieval confidence using distance values (lower is better in Chroma).
    distances = retrieval.get("distances", [[]])[0]
    top_score = 1.0 - (min(distances) if distances else 1.0)
    _logger.info("retrieval_top_score=%.2f", top_score)

    if 0.70 <= top_score <= 0.82:
        clarification = detect_missing_fields(query, session.pet_profile)
        if clarification:
            questions = generate_questions(llm, query, clarification, route.intent)
            return ChatResponse(
                text="I need a few details to help.",
                follow_up_questions=questions,
            )

    if config.live_search_enabled and _use_live_search(query, top_score, config.retrieval_confidence_threshold):
        allowlist = load_domain_allowlist(config.domain_allowlist_path)
        try:
            results = live_search(
                query,
                api_key=config.serper_api_key,
                allowlist=allowlist,
                endpoint=config.serper_endpoint,
            )
        except LiveSearchError:
            results = []
        live_summary = _format_live_search_results(results)
        if live_summary:
            rag_text = f"{rag_text}\n\n{live_summary}"
            citations.extend(
                [
                    {
                        "source_title": r.title,
                        "organization": r.source_domain,
                        "publication_year": None,
                        "section_reference": "",
                        "url": r.link,
                    }
                    for r in results[:5]
                ]
            )
        else:
            fallback_prompt = compose_prompt("prompts/fallback_prompt.txt", question=query)
            vet_response = _validate_llm_response(fallback_prompt, llm)
            answer = format_vet_response(vet_response)
            answer = apply_safety_guardrails(answer)
            response = ChatResponse(
                text=answer,
                citations=[],
                vet_response=vet_response.model_dump(),
            )
            _response_cache.set(query.lower(), response)
            return response

    prompt = compose_prompt("prompts/rag_prompt.txt", context=rag_text, question=query)
    vet_response = _validate_llm_response(prompt, llm)
    if citations:
        vet_response.citations = validate_kb_citations(
            citations, allowed_titles, min_similarity=0.75
        )
    answer = format_vet_response(vet_response)
    answer = apply_safety_guardrails(answer)
    response = ChatResponse(
        text=answer,
        citations=[c.model_dump() for c in vet_response.citations],
        vet_response=vet_response.model_dump(),
    )
    _response_cache.set(response_key, response)
    return response
