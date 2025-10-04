#from __future__ import annotations

import time
from urllib.parse import quote

import requests

from .clients import USER_AGENT

API_BASE = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
DEFAULT_PROJECT = "en.wikipedia.org"
DEFAULT_ACCESS = "all-access"
DEFAULT_AGENT = "user"
DEFAULT_GRANULARITY = "monthly"

def encode_title_for_api(title: str) -> str:
    """Encode a Wikipedia title for use in the REST API."""
    return quote(title.replace(" ", "_"), safe="")


def get_yearly_total_views(
    session: requests.Session,
    title: str,
    start: str,
    end: str,
    project: str = DEFAULT_PROJECT,
    access: str = DEFAULT_ACCESS,
    agent: str = DEFAULT_AGENT,
    granularity: str = DEFAULT_GRANULARITY,
) -> int:
    """
    Return the total pageviews for a single title across a time range.

    start/end must be YYYYMMDD (inclusive start, exclusive end for monthly granularity).
    Example monthly range: start="20240801", end="20250701".
    """
    encoded_title = encode_title_for_api(title)
    url = f"{API_BASE}/{project}/{access}/{agent}/{encoded_title}/{granularity}/{start}/{end}"
    headers = {"User-Agent": USER_AGENT}

    backoff_seconds = 1.0
    for _attempt in range(6):
        response = session.get(url, headers=headers, timeout=30)
        if response.status_code == 404:
            # No data for the page/title in this period.
            return 0
        if response.ok:
            payload = response.json()
            return sum(point.get("views", 0) for point in payload.get("items", []))
        time.sleep(backoff_seconds)
        backoff_seconds = min(backoff_seconds * 2, 30.0)

    response.raise_for_status()
    return 0
