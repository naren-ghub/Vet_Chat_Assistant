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


def _install_fake_genai(model):
    fake = types.SimpleNamespace()
    fake.configure = lambda api_key=None: None
    fake.GenerativeModel = lambda name: model
    sys.modules["google.generativeai"] = fake


def test_llm_generate_success():
    model = DummyModel()
    _install_fake_genai(model)
    client = GeminiClient("key", "model", 0.2, 256, 0.9)
    assert client.generate("hi") == "response"
    assert model.calls == 1


def test_llm_generate_retries():
    model = DummyModel(fail_times=2)
    _install_fake_genai(model)
    client = GeminiClient("key", "model", 0.2, 256, 0.9)
    assert client.generate("hi") == "response"
    assert model.calls == 3
