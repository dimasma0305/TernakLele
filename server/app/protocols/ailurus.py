import requests
import logging

from models import FlagStatus, SubmitResult

logger = logging.getLogger(__name__)

RESPONSES = {
    "flag is correct.": FlagStatus.ACCEPTED,
    "flag already submitted.": FlagStatus.REJECTED,
    "flag is wrong or expired.": FlagStatus.REJECTED,
}

API_TIMEOUT = 5


def submit_flags(flags, config):
    """
    Submit flags ke Ailurus API v2.

    config wajib berisi:
      - SYSTEM_URL (contoh: http://127.0.0.1:5000)
      - TEAM_TOKEN (JWT team token)
    """

    url = f"{config['SYSTEM_URL'].rstrip('/')}/api/v2/submit"
    headers = {
        "Authorization": f"Bearer {config['TEAM_TOKEN']}",
        "Content-Type": "application/json",
    }

    payload = {"flags": [f.flag for f in flags]}

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=API_TIMEOUT)
    except requests.RequestException as e:
        logger.error("HTTP request error: %s", e)
        for f in flags:
            yield SubmitResult(f.flag, FlagStatus.QUEUED, str(e))
        return

    if r.status_code != 200:
        logger.error("Unexpected status code %s: %s", r.status_code, r.text)
        for f in flags:
            yield SubmitResult(f.flag, FlagStatus.QUEUED, f"HTTP {r.status_code}")
        return

    try:
        resp = r.json()
    except ValueError:
        logger.error("Invalid JSON response: %s", r.text)
        for f in flags:
            yield SubmitResult(f.flag, FlagStatus.QUEUED, "invalid json")
        return

    if "data" not in resp:
        logger.error("Unexpected response format: %s", resp)
        for f in flags:
            yield SubmitResult(f.flag, FlagStatus.QUEUED, "bad format")
        return

    results = resp["data"]

    for i, f in enumerate(flags):
        if i < len(results):
            res = results[i]
            verdict = res.get("verdict", "").lower().strip()
            message = res.get("verdict", "")

            # Cari mapping verdict
            status = None
            for key, val in RESPONSES.items():
                if verdict == key.lower():
                    status = val
                    break
            
            yield SubmitResult(f.flag, status, message)
        else:
            yield SubmitResult(f.flag, FlagStatus.QUEUED, "missing response")
