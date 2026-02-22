from __future__ import annotations

import urllib.parse


def build_map_link(location_query: str) -> str:
    query = urllib.parse.quote_plus(location_query)
    return f"https://www.google.com/maps/search/?api=1&query={query}"
