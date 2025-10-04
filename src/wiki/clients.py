import time
import requests

MEDIAWIKI_API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "ad-hoc script (contact: User:SnowFire)"

def mw_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def mw_get(params: dict, session: requests.Session) -> dict:
    params = {**params, "format": "json"}
    backoff_seconds = 1.0
    for _attempt in range(6):
        response = session.get(MEDIAWIKI_API, params=params, timeout=30)
        if response.status_code == 200:
            payload = response.json()
            if "error" in payload:
                raise RuntimeError(payload["error"])
            return payload
        time.sleep(backoff_seconds)
        backoff_seconds = min(backoff_seconds * 2, 30.0)
    response.raise_for_status()
    raise RuntimeError("Unreachable")
