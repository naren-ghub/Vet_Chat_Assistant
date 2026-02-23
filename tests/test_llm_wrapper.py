import json

import requests

from core.llm_groq import GroqClient


class DummyResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_llm_generate_success(monkeypatch):
    def fake_post(url, json=None, headers=None, timeout=None):
        assert url.endswith("/chat/completions")
        return DummyResponse(
            200,
            {
                "choices": [{"message": {"content": "response"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            },
        )

    monkeypatch.setattr(requests, "post", fake_post)
    client = GroqClient("key", "llama-3.1-8b-instant", 0.2, 256, 0.9, 5)
    assert client.generate("hi") == "response"


def test_llm_generate_retries(monkeypatch):
    calls = {"n": 0}

    def fake_post(url, json=None, headers=None, timeout=None):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise RuntimeError("temporary failure")
        return DummyResponse(
            200,
            {
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            },
        )

    monkeypatch.setattr(requests, "post", fake_post)
    client = GroqClient("key", "llama-3.1-8b-instant", 0.2, 256, 0.9, 5)
    assert client.generate("hi") == "ok"
    assert calls["n"] == 3

