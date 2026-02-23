from fastapi.testclient import TestClient
import importlib

class DummyLLM:
    def generate(self, prompt: str, **kwargs) -> str:
        return (
            '{'
            '"answer":"Test response",'
            '"possible_causes":"Test causes",'
            '"warning_signs":"Test warnings",'
            '"vet_visit_guidance":"Test guidance",'
            '"care_tips":"Test tips",'
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


def test_chat_endpoint_mocked(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "x")
    monkeypatch.setenv("SERPER_API_KEY", "x")

    app_module = importlib.import_module("api.app")
    app_module = importlib.reload(app_module)

    monkeypatch.setattr(app_module, "build_llm_client", lambda *args, **kwargs: DummyLLM())
    monkeypatch.setattr(app_module, "BGEEmbedder", lambda *args, **kwargs: DummyEmbedder())
    monkeypatch.setattr(app_module, "get_collection", lambda *args, **kwargs: DummyCollection())

    client = TestClient(app_module.app)
    payload = {"session_id": "s1", "message": "my dog is vomiting"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["vet_response"]["answer"] == "Test response"
