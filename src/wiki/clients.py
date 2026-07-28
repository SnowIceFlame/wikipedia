import time
import requests

MEDIAWIKI_API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "ad-hoc script (contact: User:SnowFire)"

def mw_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def mw_get(params: dict, session: requests.Session, delay: float = 0.1) -> dict:
    params = {**params, "format": "json"}
    backoff_seconds = 1.0
    for attempt in range(10):
        if delay > 0:
            time.sleep(delay)
        response = session.get(MEDIAWIKI_API, params=params, timeout=30)
        if response.status_code == 200:
            payload = response.json()
            if "error" in payload:
                raise RuntimeError(payload["error"])
            return payload

        if response.status_code in (429, 500, 502, 503, 504):
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    sleep_time = float(retry_after)
                except ValueError:
                    sleep_time = backoff_seconds
            else:
                sleep_time = backoff_seconds
            time.sleep(sleep_time)
            backoff_seconds = min(backoff_seconds * 2, 60.0)
        else:
            response.raise_for_status()

    response.raise_for_status()
    raise RuntimeError("Unreachable")
