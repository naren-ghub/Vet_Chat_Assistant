from __future__ import annotations

from pathlib import Path


def load_prompt(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def compose_prompt(body_path: str, **kwargs) -> str:
    master = load_prompt("prompts/master_prompt.txt")
    body = load_prompt(body_path).format(**kwargs)
    return f"{master}\n\n{body}"
