import sys
import types

from core.llm import GeminiClient


class DummyResponse:
    def __init__(self, text="ok"):
        self.text = text
        self.usage_metadata = None


class DummyModel:
    def __init__(self, fail_times=0):
        self._fail_times = fail_times
        self.calls = 0

    def generate_content(self, prompt, generation_config=None):
        self.calls += 1
        if self.calls <= self._fail_times:
            raise RuntimeError("temporary failure")
        return DummyResponse(text="response")


class DummyClient:
    def __init__(self, model):
        self.models = types.SimpleNamespace(
            generate_content=lambda **kwargs: model.generate_content(
                kwargs.get("contents"), kwargs.get("config")
            )
        )


def _install_fake_genai(monkeypatch, model):
    types_mod = types.SimpleNamespace(
        HttpOptions=lambda **kwargs: kwargs,
        GenerateContentConfig=lambda **kwargs: kwargs,
    )
    genai_mod = types.SimpleNamespace(Client=lambda **kwargs: DummyClient(model), types=types_mod)
    google_mod = types.SimpleNamespace(genai=genai_mod)
    monkeypatch.setitem(sys.modules, "google", google_mod)
    monkeypatch.setitem(sys.modules, "google.genai", genai_mod)
    monkeypatch.setitem(sys.modules, "google.genai.types", types_mod)


def test_llm_generate_success(monkeypatch):
    model = DummyModel()
    _install_fake_genai(monkeypatch, model)
    client = GeminiClient("key", "model", 0.2, 256, 0.9, 5)
    assert client.generate("hi") == "response"
    assert model.calls == 1


def test_llm_generate_retries(monkeypatch):
    model = DummyModel(fail_times=2)
    _install_fake_genai(monkeypatch, model)
    client = GeminiClient("key", "model", 0.2, 256, 0.9, 5)
    assert client.generate("hi") == "response"
    assert model.calls == 3
