from __future__ import annotations

from pathlib import Path


def load_prompt(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _safe_format(template: str, **kwargs) -> str:
    escaped = template.replace("{", "{{").replace("}", "}}")
    for key in kwargs.keys():
        escaped = escaped.replace(f"{{{{{key}}}}}", f"{{{key}}}")
    return escaped.format(**kwargs)


def compose_prompt(body_path: str, **kwargs) -> str:
    master = load_prompt("prompts/master_prompt.txt")
    body = _safe_format(load_prompt(body_path), **kwargs)
    return f"{master}\n\n{body}"
