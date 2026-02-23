from __future__ import annotations

from typing import List

import json
import re

from core.cache import TTLCache
from core.config import AppConfig, load_domain_allowlist
from core.errors import LiveSearchError, VectorDBError
from core.llm_base import LLMClient, LLMConfig
from core.llm_policy import select_llm_config
from core.llm_provider import build_llm_client
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
from core.safety import DOSAGE_PATTERN, apply_safety_guardrails
from core.types import ChatResponse, SessionState
from core.intent import emergency_score, has_immediate_override
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
_TOXIC_KEYWORDS = {
    "poison",
    "toxic",
    "ingestion",
    "chocolate",
    "xylitol",
    "grape",
    "grapes",
    "raisin",
    "raisins",
    "antifreeze",
}
_SYMPTOM_KEYWORDS = {
    "vomit",
    "vomiting",
    "diarrhea",
    "lethargic",
    "lethargy",
    "not eating",
    "no appetite",
    "cough",
    "sneeze",
    "fever",
    "bleeding",
    "pain",
    "swollen",
}
_ACADEMIC_PHRASES = {
    "standard dosage",
    "usual dose",
    "recommended mg/kg",
    "in veterinary medicine",
    "for academic",
    "for study",
    "textbook",
}
_CONCEPTUAL_STARTS = (
    "why",
    "what",
    "how",
    "explain",
    "tell me about",
)
_WEIGHT_PATTERN = re.compile(r"\b\d+(\.\d+)?\s*(kg|kgs|lb|lbs|pounds)\b", re.I)
_AGE_PATTERN = re.compile(r"\b\d+\s*(week|weeks|month|months|year|years)\b", re.I)
_PROMPT_LEAK_PATTERNS = [
    re.compile(r"\bprompt_version\s*=", re.I),
    re.compile(r"\blast_updated_date\s*=", re.I),
    re.compile(r"\bowner\s*=", re.I),
    re.compile(r"\bmaster system prompt\b", re.I),
    re.compile(r"\byou are a veterinary assistance ai\b", re.I),
]


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


def _hybrid_allowed(query: str, emergency_threshold: float) -> bool:
    lowered = query.lower()
    if has_immediate_override(query):
        return False
    if emergency_score(query) >= emergency_threshold:
        return False
    if DOSAGE_PATTERN.search(query):
        return False
    if any(keyword in lowered for keyword in _TOXIC_KEYWORDS):
        return False
    return True


def _determine_response_mode(
    intent: str,
    top_score: float,
    emergency_score_value: float,
    emergency_threshold: float,
    hybrid_allowed: bool,
) -> str:
    if emergency_score_value >= emergency_threshold:
        return "emergency"
    if top_score > 0.82:
        return "full_rag"
    if 0.70 <= top_score <= 0.82:
        if intent in {"vaccination", "pet_care", "general_info"} and hybrid_allowed:
            return "hybrid_partial"
        return "clarification_required"
    return "live_search"


def _format_live_search_results(results) -> str:
    if not results:
        return ""
    lines = ["Live search summary:"]
    for r in results[:5]:
        lines.append(f"- {r.title} ({r.source_domain}): {r.snippet}")
    return "\n".join(lines)


def _llm_generate(
    llm: LLMClient,
    prompt: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
    log_meta: dict | None = None,
) -> str:
    cache_key = json.dumps(
        {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        },
        sort_keys=True,
    )
    cached = _llm_cache.get(cache_key)
    if cached:
        return cached
    if log_meta:
        _logger.info(
            "llm_call model=%s query_context=%s response_style=%s response_mode=%s temperature=%s max_tokens=%s top_p=%s",
            getattr(llm, "model_name", "unknown"),
            log_meta.get("query_context"),
            log_meta.get("response_style"),
            log_meta.get("response_mode"),
            temperature,
            max_tokens,
            top_p,
        )
    text = llm.generate(prompt, temperature=temperature, max_tokens=max_tokens, top_p=top_p)
    _llm_cache.set(cache_key, text)
    return text


def _embed_query(embedder: BGEEmbedder, query: str):
    cached = _embedding_cache.get(query)
    if cached is not None:
        return cached
    vec = embedder.encode([query])[0]
    _embedding_cache.set(query, vec)
    return vec


def _validate_llm_response(
    prompt: str,
    llm: LLMClient,
    llm_config: LLMConfig,
    log_meta: dict | None = None,
) -> VetResponse:
    text = _llm_generate(
        llm,
        prompt,
        temperature=llm_config.temperature,
        max_tokens=llm_config.max_tokens,
        top_p=llm_config.top_p,
        log_meta=log_meta,
    )
    parsed = parse_vet_response(text)
    if parsed:
        return parsed
    retry_prompt = prompt + "\n\nReturn ONLY valid JSON that matches the schema."
    text = _llm_generate(
        llm,
        retry_prompt,
        temperature=llm_config.temperature,
        max_tokens=llm_config.max_tokens,
        top_p=llm_config.top_p,
        log_meta=log_meta,
    )
    parsed = parse_vet_response(text)
    if parsed:
        return parsed
    return fallback_vet_response()


def _determine_query_context(query: str, pet_profile: dict) -> str:
    lowered = query.lower()
    if any(tag in lowered for tag in ["my dog", "my cat", "my puppy", "my kitten", "my pet"]):
        return "CLINICAL_SPECIFIC"
    if _WEIGHT_PATTERN.search(query):
        return "CLINICAL_SPECIFIC"
    if _AGE_PATTERN.search(query) and "old" in lowered:
        return "CLINICAL_SPECIFIC"
    if any(keyword in lowered for keyword in _SYMPTOM_KEYWORDS):
        return "CLINICAL_SPECIFIC"
    if any(keyword in lowered for keyword in ["right now", "immediately", "asap", "today"]):
        return "CLINICAL_SPECIFIC"
    if any(keyword in lowered for keyword in ["how much should i give", "dose for", "dosage for"]):
        return "CLINICAL_SPECIFIC"
    if pet_profile.get("age") or pet_profile.get("weight"):
        return "CLINICAL_SPECIFIC"
    if any(phrase in lowered for phrase in _ACADEMIC_PHRASES):
        return "ACADEMIC"
    return "GENERAL"


def _determine_response_style(
    intent: str,
    query: str,
    emergency_score_value: float,
    emergency_threshold: float,
    query_context: str,
) -> str:
    lowered = query.lower()
    if emergency_score_value >= emergency_threshold:
        return "clinical"
    if query_context == "CLINICAL_SPECIFIC":
        return "clinical"
    if intent not in {"vaccination", "pet_care", "general_info"}:
        return "clinical"
    if any(keyword in lowered for keyword in _SYMPTOM_KEYWORDS):
        return "clinical"
    if any(keyword in lowered for keyword in _TOXIC_KEYWORDS):
        return "clinical"
    if DOSAGE_PATTERN.search(query) and query_context == "CLINICAL_SPECIFIC":
        return "clinical"
    stripped = lowered.strip()
    if any(stripped.startswith(starter) for starter in _CONCEPTUAL_STARTS):
        return "educational"
    return "clinical"


def _has_prompt_leak(text: str) -> bool:
    return any(p.search(text) for p in _PROMPT_LEAK_PATTERNS)


def _override_if_unsafe(text: str, query_context: str) -> str:
    # Prevent leaking system/prompt content in any context.
    if _has_prompt_leak(text):
        return (
            "I can’t share system instructions. If you tell me your pet’s species, age, and symptoms, "
            "I can help with safe guidance."
        )

    # Post-generation safety net: no dosing instructions for real pet cases.
    if (query_context or "").upper() == "CLINICAL_SPECIFIC" and DOSAGE_PATTERN.search(text):
        return (
            "Safety note: I can’t provide medication dosages for a specific animal. "
            "Please contact a licensed veterinarian for dosing guidance."
        )

    return text


def chat(
    query: str,
    session: SessionState,
    config: AppConfig,
    llm_client=None,
    embedder=None,
    collection=None,
) -> ChatResponse:
    llm: LLMClient = llm_client or build_llm_client(config)
    embedder = embedder or BGEEmbedder(config.bge_model)
    if collection is None:
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
    emergency_score_value = emergency_score(query)
    query_context = _determine_query_context(query, session.pet_profile)
    response_style = _determine_response_style(
        route.intent, query, emergency_score_value, config.emergency_threshold, query_context
    )
    _logger.info("emergency_score=%.2f", emergency_score_value)
    session.last_intent = route.intent
    _logger.info("intent=%s confidence=%.2f route=%s", route.intent, route.confidence, route.route)

    if route.route == "clinic_search":
        link = build_map_link("veterinary clinic")
        return ChatResponse(
            text="Here is a nearby veterinary clinic search link.",
            map_link=link,
            response_mode="clinic_locator",
            response_style=response_style,
            query_context=query_context,
            emergency_flag=False,
        )

    if route.route == "emergency" or is_emergency(query, config.emergency_threshold):
        prompt = compose_prompt("prompts/emergency_prompt.txt", question=query)
        llm_cfg = select_llm_config("CLINICAL_SPECIFIC", "clinical", config)
        vet_response = _validate_llm_response(
            prompt,
            llm,
            llm_cfg,
            log_meta={
                "query_context": "CLINICAL_SPECIFIC",
                "response_style": "clinical",
                "response_mode": "emergency",
            },
        )
        vet_response.citations = []
        answer = format_vet_response(vet_response)
        answer = apply_safety_guardrails(answer)
        answer = _override_if_unsafe(answer, query_context)
        return ChatResponse(
            text=answer,
            emergency=True,
            vet_response=vet_response.model_dump(),
            response_mode="emergency",
            response_style="clinical",
            query_context=query_context,
            emergency_flag=True,
        )

    profile_key = json.dumps(session.pet_profile, sort_keys=True, default=str)
    response_key = (
        f"{query.lower()}|{profile_key}|{session.last_intent or ''}|"
        f"{query_context}|{response_style}"
    )
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
    hybrid_allowed = _hybrid_allowed(query, config.emergency_threshold)
    response_mode = _determine_response_mode(
        route.intent,
        top_score,
        emergency_score_value,
        config.emergency_threshold,
        hybrid_allowed,
    )

    force_live_search = "latest" in query.lower() or "recent" in query.lower()
    if config.live_search_enabled and force_live_search:
        response_mode = "live_search"

    llm_cfg = select_llm_config(query_context, response_style, config)

    if response_style == "educational":
        live_search_flag = False
        if config.live_search_enabled and force_live_search:
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
                live_search_flag = True
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
        prompt = compose_prompt(
            "prompts/educational_prompt.txt",
            question=query,
            context=rag_text,
            query_context=query_context,
        )
        text = _llm_generate(
            llm,
            prompt,
            temperature=llm_cfg.temperature,
            max_tokens=llm_cfg.max_tokens,
            top_p=llm_cfg.top_p,
            log_meta={
                "query_context": query_context,
                "response_style": response_style,
                "response_mode": response_mode,
            },
        )
        text = _override_if_unsafe(text, query_context)
        validated_citations = (
            validate_kb_citations(citations, allowed_titles, min_similarity=0.75)
            if citations
            else []
        )
        response = ChatResponse(
            text=text,
            citations=[c.model_dump() for c in validated_citations],
            response_mode=response_mode,
            response_style=response_style,
            query_context=query_context,
            live_search_flag=live_search_flag,
            emergency_flag=False,
        )
        _response_cache.set(response_key, response)
        return response

    if response_mode == "clarification_required":
        missing = detect_missing_fields(query, session.pet_profile)
        guidance, questions = generate_questions(
            llm,
            query,
            missing,
            route.intent,
            llm_config=llm_cfg,
            log_meta={
                "query_context": query_context,
                "response_style": response_style,
                "response_mode": response_mode,
            },
        )
        text = guidance.strip() if guidance else "I need a few details to help."
        text = _override_if_unsafe(text, query_context)
        return ChatResponse(
            text=text,
            follow_up_questions=questions,
            response_mode=response_mode,
            response_style=response_style,
            query_context=query_context,
            emergency_flag=False,
        )

    if response_mode == "hybrid_partial":
        missing = detect_missing_fields(query, session.pet_profile)
        guidance, questions = generate_questions(
            llm,
            query,
            missing,
            route.intent,
            llm_config=llm_cfg,
            log_meta={
                "query_context": query_context,
                "response_style": response_style,
                "response_mode": response_mode,
            },
        )
        prompt = compose_prompt(
            "prompts/rag_prompt.txt",
            user_question=query,
            retrieved_context=rag_text,
            pet_type=session.pet_profile.get("species", ""),
            conversation_context="",
            query_context=query_context,
        )
        vet_response = _validate_llm_response(
            prompt,
            llm,
            llm_cfg,
            log_meta={
                "query_context": query_context,
                "response_style": response_style,
                "response_mode": response_mode,
            },
        )
        if citations:
            vet_response.citations = validate_kb_citations(
                citations, allowed_titles, min_similarity=0.75
            )
        answer = format_vet_response(vet_response)
        answer = apply_safety_guardrails(answer)
        answer = _override_if_unsafe(answer, query_context)
        response = ChatResponse(
            text=answer,
            citations=[c.model_dump() for c in vet_response.citations],
            follow_up_questions=questions,
            vet_response=vet_response.model_dump(),
            response_mode=response_mode,
            response_style=response_style,
            query_context=query_context,
            emergency_flag=False,
        )
        _response_cache.set(response_key, response)
        return response

    live_search_flag = False
    if response_mode == "live_search" and config.live_search_enabled:
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
        live_search_flag = bool(live_summary)
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
            fallback_prompt = compose_prompt(
                "prompts/fallback_prompt.txt",
                question=query,
                query_context=query_context,
            )
            vet_response = _validate_llm_response(
                fallback_prompt,
                llm,
                llm_cfg,
                log_meta={
                    "query_context": query_context,
                    "response_style": response_style,
                    "response_mode": response_mode,
                },
            )
            answer = format_vet_response(vet_response)
            answer = apply_safety_guardrails(answer)
            answer = _override_if_unsafe(answer, query_context)
            response = ChatResponse(
                text=answer,
                citations=[],
                vet_response=vet_response.model_dump(),
                response_mode=response_mode,
                response_style=response_style,
                query_context=query_context,
                live_search_flag=live_search_flag,
                emergency_flag=False,
            )
            _response_cache.set(query.lower(), response)
            return response

    if response_mode == "live_search" and not config.live_search_enabled:
        fallback_prompt = compose_prompt(
            "prompts/fallback_prompt.txt",
            question=query,
            query_context=query_context,
        )
        vet_response = _validate_llm_response(
            fallback_prompt,
            llm,
            llm_cfg,
            log_meta={
                "query_context": query_context,
                "response_style": response_style,
                "response_mode": response_mode,
            },
        )
        answer = format_vet_response(vet_response)
        answer = apply_safety_guardrails(answer)
        answer = _override_if_unsafe(answer, query_context)
        response = ChatResponse(
            text=answer,
            citations=[],
            vet_response=vet_response.model_dump(),
            response_mode=response_mode,
            response_style=response_style,
            query_context=query_context,
            live_search_flag=live_search_flag,
            emergency_flag=False,
        )
        _response_cache.set(query.lower(), response)
        return response

    prompt = compose_prompt(
        "prompts/rag_prompt.txt",
        user_question=query,
        retrieved_context=rag_text,
        pet_type=session.pet_profile.get("species", ""),
        conversation_context="",
        query_context=query_context,
    )
    vet_response = _validate_llm_response(
        prompt,
        llm,
        llm_cfg,
        log_meta={
            "query_context": query_context,
            "response_style": response_style,
            "response_mode": response_mode,
        },
    )
    if citations:
        vet_response.citations = validate_kb_citations(
            citations, allowed_titles, min_similarity=0.75
        )
    answer = format_vet_response(vet_response)
    answer = apply_safety_guardrails(answer)
    answer = _override_if_unsafe(answer, query_context)
    response = ChatResponse(
        text=answer,
        citations=[c.model_dump() for c in vet_response.citations],
        vet_response=vet_response.model_dump(),
        response_mode=response_mode if response_mode in {"full_rag", "live_search"} else "full_rag",
        response_style=response_style,
        query_context=query_context,
        live_search_flag=live_search_flag,
        emergency_flag=False,
    )
    _response_cache.set(response_key, response)
    return response
