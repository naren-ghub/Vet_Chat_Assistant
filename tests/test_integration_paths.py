from core.chat import chat
from core.config import AppConfig
from core.types import SessionState


class DummyLLM:
    def __init__(self):
        self.calls = []

    def generate(self, prompt: str, **kwargs) -> str:
        self.calls.append(prompt)
        return (
            '{'
            '"answer":"ok",'
            '"possible_causes":"x",'
            '"warning_signs":"y",'
            '"vet_visit_guidance":"z",'
            '"care_tips":"t",'
            '"citations":[]'
            '}'
        )


class DummyEmbedder:
    def encode(self, texts):
        return [[0.1, 0.1, 0.1]]


class DummyCollection:
    def query(self, *args, **kwargs):
        return {
            "documents": [["ctx"]],
            "metadatas": [[{"source_title": "WSAVA"}]],
            "distances": [[0.1]],
        }


def _chat_module():
    import importlib

    return importlib.import_module("core.chat")


def test_emergency_override_path(monkeypatch):
    chat_module = _chat_module()

    monkeypatch.setattr(chat_module, "GeminiClient", lambda *args, **kwargs: DummyLLM())
    monkeypatch.setattr(chat_module, "BGEEmbedder", lambda *args, **kwargs: DummyEmbedder())
    monkeypatch.setattr(chat_module, "get_collection", lambda *args, **kwargs: DummyCollection())

    cfg = AppConfig(
        gemini_api_key="x",
        gemini_model="m",
        llm_temperature=0.2,
        llm_max_tokens=512,
        llm_top_p=0.9,
        llm_timeout_seconds=5,
        bge_model="b",
        chroma_path="data/chroma",
        serper_api_key="s",
        serper_endpoint="http://example",
        domain_allowlist_path="domain.txt",
        chunk_size=800,
        chunk_overlap=160,
        top_k=5,
        retrieval_confidence_threshold=0.7,
        intent_high_threshold=0.82,
        intent_medium_threshold=0.65,
        emergency_threshold=8.0,
        live_search_enabled=True,
    )
    session = SessionState(session_id="s1")
    response = chat("my dog is not breathing", session, cfg)
    assert response.emergency is True


def test_live_search_fallback_path(monkeypatch):
    chat_module = _chat_module()

    monkeypatch.setattr(chat_module, "GeminiClient", lambda *args, **kwargs: DummyLLM())
    monkeypatch.setattr(chat_module, "BGEEmbedder", lambda *args, **kwargs: DummyEmbedder())
    monkeypatch.setattr(chat_module, "get_collection", lambda *args, **kwargs: DummyCollection())
    monkeypatch.setattr(chat_module, "live_search", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        chat_module,
        "query_collection",
        lambda *args, **kwargs: {
            "documents": [["ctx"]],
            "metadatas": [[{"source_title": "WSAVA"}]],
            "distances": [[0.4]],
        },
    )

    cfg = AppConfig(
        gemini_api_key="x",
        gemini_model="m",
        llm_temperature=0.2,
        llm_max_tokens=512,
        llm_top_p=0.9,
        llm_timeout_seconds=5,
        bge_model="b",
        chroma_path="data/chroma",
        serper_api_key="s",
        serper_endpoint="http://example",
        domain_allowlist_path="domain.txt",
        chunk_size=800,
        chunk_overlap=160,
        top_k=5,
        retrieval_confidence_threshold=0.7,
        intent_high_threshold=0.82,
        intent_medium_threshold=0.65,
        emergency_threshold=8.0,
        live_search_enabled=True,
    )
    session = SessionState(session_id="s2")
    response = chat("latest rabies guidance", session, cfg)
    assert response.text.startswith("Answer:")


def test_metadata_aware_retrieval_cache_key(monkeypatch):
    chat_module = _chat_module()

    keys = []

    def capture_get(key):
        keys.append(key)
        return None

    monkeypatch.setattr(chat_module._retrieval_cache, "get", capture_get)
    monkeypatch.setattr(chat_module, "GeminiClient", lambda *args, **kwargs: DummyLLM())
    monkeypatch.setattr(chat_module, "BGEEmbedder", lambda *args, **kwargs: DummyEmbedder())
    monkeypatch.setattr(chat_module, "get_collection", lambda *args, **kwargs: DummyCollection())
    from core.types import RouteDecision
    monkeypatch.setattr(chat_module, "route_intent", lambda *args, **kwargs: RouteDecision("medical_query", 0.9, "medical_query"))
    monkeypatch.setattr(chat_module, "detect_missing_fields", lambda *args, **kwargs: [])

    cfg = AppConfig(
        gemini_api_key="x",
        gemini_model="m",
        llm_temperature=0.2,
        llm_max_tokens=512,
        llm_top_p=0.9,
        llm_timeout_seconds=5,
        bge_model="b",
        chroma_path="data/chroma",
        serper_api_key="s",
        serper_endpoint="http://example",
        domain_allowlist_path="domain.txt",
        chunk_size=800,
        chunk_overlap=160,
        top_k=5,
        retrieval_confidence_threshold=0.7,
        intent_high_threshold=0.82,
        intent_medium_threshold=0.65,
        emergency_threshold=8.0,
        live_search_enabled=False,
    )

    session_a = SessionState(session_id="s-a")
    session_a.pet_profile["species"] = "dog"
    chat("vomiting", session_a, cfg)

    session_b = SessionState(session_id="s-b")
    session_b.pet_profile["species"] = "cat"
    chat("vomiting", session_b, cfg)

    assert len(keys) >= 2
    assert keys[-2] != keys[-1]


def test_species_filter_applied(monkeypatch):
    chat_module = _chat_module()

    captured = {}

    def capture_query_collection(*args, **kwargs):
        captured["where"] = kwargs.get("where")
        return {
            "documents": [["ctx"]],
            "metadatas": [[{"source_title": "WSAVA"}]],
            "distances": [[0.1]],
        }

    from core.types import RouteDecision

    cfg = AppConfig(
        gemini_api_key="x",
        gemini_model="m",
        llm_temperature=0.2,
        llm_max_tokens=512,
        llm_top_p=0.9,
        llm_timeout_seconds=5,
        bge_model="b",
        chroma_path="data/chroma",
        serper_api_key="s",
        serper_endpoint="http://example",
        domain_allowlist_path="domain.txt",
        chunk_size=800,
        chunk_overlap=160,
        top_k=5,
        retrieval_confidence_threshold=0.7,
        intent_high_threshold=0.82,
        intent_medium_threshold=0.65,
        emergency_threshold=8.0,
        live_search_enabled=False,
    )
    session = SessionState(session_id="s3")
    session.pet_profile["species"] = "dog"
    filters = chat_module.build_where_filters(session, RouteDecision("medical_query", 0.9, "medical_query"))
    assert filters == {"$or": [{"species": "dog"}, {"species": "all"}]}


def test_hybrid_partial_informational(monkeypatch):
    chat_module = _chat_module()

    called = {"questions": False}

    def capture_query_collection(*args, **kwargs):
        return {
            "documents": [["ctx"]],
            "metadatas": [[{"source_title": "WSAVA"}]],
            "distances": [[0.25]],
        }

    from core.types import RouteDecision

    monkeypatch.setattr(chat_module, "GeminiClient", lambda *args, **kwargs: DummyLLM())
    monkeypatch.setattr(chat_module, "BGEEmbedder", lambda *args, **kwargs: DummyEmbedder())
    monkeypatch.setattr(chat_module, "get_collection", lambda *args, **kwargs: DummyCollection())
    monkeypatch.setattr(chat_module, "query_collection", capture_query_collection)
    monkeypatch.setattr(chat_module, "route_intent", lambda *args, **kwargs: RouteDecision("vaccination", 0.9, "medical_query"))

    def fake_questions(*args, **kwargs):
        called["questions"] = True
        return "", ["What is your pet's age?"]

    monkeypatch.setattr(chat_module, "generate_questions", fake_questions)
    monkeypatch.setattr(chat_module, "detect_missing_fields", lambda *args, **kwargs: ["age"])

    cfg = AppConfig(
        gemini_api_key="x",
        gemini_model="m",
        llm_temperature=0.2,
        llm_max_tokens=512,
        llm_top_p=0.9,
        llm_timeout_seconds=5,
        bge_model="b",
        chroma_path="data/chroma",
        serper_api_key="s",
        serper_endpoint="http://example",
        domain_allowlist_path="domain.txt",
        chunk_size=800,
        chunk_overlap=160,
        top_k=5,
        retrieval_confidence_threshold=0.7,
        intent_high_threshold=0.82,
        intent_medium_threshold=0.65,
        emergency_threshold=8.0,
        live_search_enabled=False,
    )
    session = SessionState(session_id="s4")
    response = chat("kitten vaccination schedule", session, cfg)
    assert called["questions"] is True
    assert response.text.startswith("Answer:")
    assert response.follow_up_questions


def test_live_search_latest_override(monkeypatch):
    chat_module = _chat_module()

    called = {"live": False}

    def capture_query_collection(*args, **kwargs):
        return {
            "documents": [["ctx"]],
            "metadatas": [[{"source_title": "WSAVA"}]],
            "distances": [[0.25]],
        }

    def fake_live_search(*args, **kwargs):
        called["live"] = True
        return []

    from core.types import RouteDecision

    monkeypatch.setattr(chat_module, "GeminiClient", lambda *args, **kwargs: DummyLLM())
    monkeypatch.setattr(chat_module, "BGEEmbedder", lambda *args, **kwargs: DummyEmbedder())
    monkeypatch.setattr(chat_module, "get_collection", lambda *args, **kwargs: DummyCollection())
    monkeypatch.setattr(chat_module, "query_collection", capture_query_collection)
    monkeypatch.setattr(chat_module, "live_search", fake_live_search)
    monkeypatch.setattr(chat_module, "route_intent", lambda *args, **kwargs: RouteDecision("general_info", 0.9, "medical_query"))

    cfg = AppConfig(
        gemini_api_key="x",
        gemini_model="m",
        llm_temperature=0.2,
        llm_max_tokens=512,
        llm_top_p=0.9,
        llm_timeout_seconds=5,
        bge_model="b",
        chroma_path="data/chroma",
        serper_api_key="s",
        serper_endpoint="http://example",
        domain_allowlist_path="domain.txt",
        chunk_size=800,
        chunk_overlap=160,
        top_k=5,
        retrieval_confidence_threshold=0.7,
        intent_high_threshold=0.82,
        intent_medium_threshold=0.65,
        emergency_threshold=8.0,
        live_search_enabled=True,
    )
    session = SessionState(session_id="s5")
    response = chat("latest rabies guidance", session, cfg)
    assert called["live"] is True
    assert response.text.startswith("Answer:")


def test_hybrid_blocked_by_toxic(monkeypatch):
    chat_module = _chat_module()

    monkeypatch.setattr(chat_module, "GeminiClient", lambda *args, **kwargs: DummyLLM())
    monkeypatch.setattr(chat_module, "BGEEmbedder", lambda *args, **kwargs: DummyEmbedder())
    monkeypatch.setattr(chat_module, "get_collection", lambda *args, **kwargs: DummyCollection())
    monkeypatch.setattr(
        chat_module,
        "query_collection",
        lambda *args, **kwargs: {
            "documents": [["ctx"]],
            "metadatas": [[{"source_title": "WSAVA"}]],
            "distances": [[0.25]],
        },
    )
    from core.types import RouteDecision
    monkeypatch.setattr(chat_module, "route_intent", lambda *args, **kwargs: RouteDecision("general_info", 0.9, "medical_query"))
    monkeypatch.setattr(chat_module, "generate_questions", lambda *args, **kwargs: ("", ["What was ingested?"]))
    monkeypatch.setattr(chat_module, "detect_missing_fields", lambda *args, **kwargs: ["substance"])

    cfg = AppConfig(
        gemini_api_key="x",
        gemini_model="m",
        llm_temperature=0.2,
        llm_max_tokens=512,
        llm_top_p=0.9,
        llm_timeout_seconds=5,
        bge_model="b",
        chroma_path="data/chroma",
        serper_api_key="s",
        serper_endpoint="http://example",
        domain_allowlist_path="domain.txt",
        chunk_size=800,
        chunk_overlap=160,
        top_k=5,
        retrieval_confidence_threshold=0.7,
        intent_high_threshold=0.82,
        intent_medium_threshold=0.65,
        emergency_threshold=8.0,
        live_search_enabled=False,
    )
    session = SessionState(session_id="s6")
    response = chat("is xylitol toxic to dogs", session, cfg)
    assert response.text == "I need a few details to help."
    assert response.follow_up_questions


def test_educational_response_style(monkeypatch):
    chat_module = _chat_module()

    class EduLLM:
        def generate(self, prompt: str, **kwargs) -> str:
            return "Educational response."

    monkeypatch.setattr(chat_module, "GeminiClient", lambda *args, **kwargs: EduLLM())
    monkeypatch.setattr(chat_module, "BGEEmbedder", lambda *args, **kwargs: DummyEmbedder())
    monkeypatch.setattr(chat_module, "get_collection", lambda *args, **kwargs: DummyCollection())
    monkeypatch.setattr(
        chat_module,
        "query_collection",
        lambda *args, **kwargs: {
            "documents": [["ctx"]],
            "metadatas": [[{"source_title": "WSAVA"}]],
            "distances": [[0.9]],
        },
    )
    from core.types import RouteDecision
    monkeypatch.setattr(chat_module, "route_intent", lambda *args, **kwargs: RouteDecision("general_info", 0.9, "medical_query"))

    cfg = AppConfig(
        gemini_api_key="x",
        gemini_model="m",
        llm_temperature=0.2,
        llm_max_tokens=512,
        llm_top_p=0.9,
        llm_timeout_seconds=5,
        bge_model="b",
        chroma_path="data/chroma",
        serper_api_key="s",
        serper_endpoint="http://example",
        domain_allowlist_path="domain.txt",
        chunk_size=800,
        chunk_overlap=160,
        top_k=5,
        retrieval_confidence_threshold=0.7,
        intent_high_threshold=0.82,
        intent_medium_threshold=0.65,
        emergency_threshold=8.0,
        live_search_enabled=False,
    )
    session = SessionState(session_id="s7")
    response = chat("why do we vaccinate animals", session, cfg)
    assert response.text == "Educational response."
    assert response.follow_up_questions == []
