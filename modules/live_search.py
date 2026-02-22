from __future__ import annotations

from typing import List

import requests

from core.types import SearchResult
from core.errors import LiveSearchError


def _domain_from_url(url: str) -> str:
    return url.split("/")[2].lower() if "://" in url else url.split("/")[0].lower()


def _domain_allowed(domain: str, allowlist: List[str]) -> bool:
    if not allowlist:
        return True
    for allowed in allowlist:
        allowed = allowed.lower()
        if domain == allowed or domain.endswith(f".{allowed}"):
            return True
    return False


def live_search(
    query: str,
    api_key: str,
    allowlist: List[str],
    endpoint: str = "https://google.serper.dev/search",
) -> List[SearchResult]:
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query, "gl": "us", "hl": "en"}
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        raise LiveSearchError("Live search failed") from exc
    items = data.get("organic", [])
    results: List[SearchResult] = []
    for item in items:
        link = item.get("link", "")
        if not link:
            continue
        domain = _domain_from_url(link)
        if not _domain_allowed(domain, allowlist):
            continue
        results.append(
            SearchResult(
                title=item.get("title", ""),
                link=link,
                snippet=item.get("snippet", ""),
                source_domain=domain,
            )
        )
    return results
