import requests
import logging
from typing import Iterable, Generator, Optional, Dict, Any

from models import FlagStatus, SubmitResult

logger = logging.getLogger(__name__)

# Mapping verdict exact -> FlagStatus (semua key sebaiknya lowercased dan trimmed)
RESPONSES: Dict[str, FlagStatus] = {
    "flag is correct.": FlagStatus.ACCEPTED,
    "flag already submitted.": FlagStatus.REJECTED,
    "flag is wrong or expired.": FlagStatus.REJECTED,
}

API_TIMEOUT = 20  # detik


def submit_flags(flags: Iterable[Any], config: Dict[str, str]):
    """
    Submit flags ke Ailurus API v2.

    Args:
        flags: iterable objek yang punya atribut `.flag` (mis. list of objects)
        config: wajib berisi:
          - SYSTEM_URL (contoh: http://127.0.0.1:5000)
          - TEAM_TOKEN (JWT team token)
        session: optional requests.Session untuk reuse koneksi (bagus untuk performa)
    Yields:
        SubmitResult untuk tiap flag
    """

    url = f"{config['SYSTEM_URL'].rstrip('/')}/api/v2/submit"
    headers = {
        "Authorization": f"Bearer {config['TEAM_TOKEN']}",
        "Content-Type": "application/json",
    }

    payload = {"flags": [f.flag for f in flags]}

    sess = requests.Session()

    try:
        r = sess.post(url, json=payload, headers=headers, timeout=API_TIMEOUT)
    except requests.RequestException as e:
        logger.error("HTTP request error: %s", e)
        # Pada error koneksi, tandai semua sebagai QUEUED (bisa di-retry nanti oleh caller)
        for f in flags:
            yield SubmitResult(f.flag, FlagStatus.QUEUED, str(e))
        return

    # Non-200 handling (server-level error / auth / rate limit / contest state)
    if r.status_code != 200:
        # coba parse JSON untuk pesan yang lebih informatif
        msg = r.text
        try:
            j = r.json()
            # API doc memakai fields "status" dan "message" untuk error responses
            msg = j.get("message", msg)
        except ValueError:
            # not json, keep raw text
            pass

        logger.warning("Unexpected status code %s: %s", r.status_code, msg)

        # Handling status-code spesifik (optional: caller bisa memperlakukan ini berbeda)
        if r.status_code == 400:
            # 400 bisa berarti contest not started / contest finished / flag not found (per API doc)
            for f in flags:
                yield SubmitResult(f.flag, FlagStatus.QUEUED, f"HTTP 400: {msg}")
            return
        elif r.status_code == 403:
            for f in flags:
                yield SubmitResult(f.flag, FlagStatus.QUEUED, f"HTTP 403: {msg}")
            return
        elif r.status_code == 429:
            for f in flags:
                yield SubmitResult(f.flag, FlagStatus.QUEUED, f"HTTP 429: {msg}")
            return
        else:
            for f in flags:
                yield SubmitResult(f.flag, FlagStatus.QUEUED, f"HTTP {r.status_code}: {msg}")
            return

    # status_code == 200: parse body
    try:
        resp = r.json()
    except ValueError:
        logger.error("Invalid JSON response: %s", r.text)
        for f in flags:
            yield SubmitResult(f.flag, FlagStatus.QUEUED, "invalid json")
        return

    # Jika response gagal format (tidak ada 'data'), coba handle sebagai error
    if "data" not in resp:
        # Ada kemungkinan API memberi 'status'='failed' dan 'message' di root
        msg = resp.get("message", str(resp))
        logger.error("Unexpected response format: %s", resp)
        for f in flags:
            yield SubmitResult(f.flag, FlagStatus.QUEUED, f"bad format: {msg}")
        return

    results = resp["data"]

    # results kemungkinan berisi list objek {"flag": "...", "verdict": "..."}
    # Kita akan match by index (sesuai doc) namun jika API mengembalikan flag per-item, gunakan itu.
    flags_list = list(flags)
    for i, f in enumerate(flags_list):
        if i < len(results):
            res = results[i] or {}
            # prefer server-returned flag jika ada (lebih aman)
            server_flag = res.get("flag")
            verdict_raw = res.get("verdict", "") or ""
            verdict = verdict_raw.lower().strip()
            message = verdict_raw or res.get("message", "") or ""

            # mapping langsung dari RESPONSES
            status = RESPONSES.get(verdict)

            # fallback heuristics jika mapping tidak cocok
            if status is None:
                if "correct" in verdict:
                    status = FlagStatus.ACCEPTED
                elif "already" in verdict or "wrong" in verdict or "expired" in verdict:
                    status = FlagStatus.REJECTED
                else:
                    # tidak tahu artinya -> taruh QUEUED supaya caller bisa retry / inspect
                    status = FlagStatus.QUEUED

            flag_value = server_flag if server_flag else f.flag
            yield SubmitResult(flag_value, status, message)
        else:
            # tidak ada response untuk flag ini
            yield SubmitResult(f.flag, FlagStatus.QUEUED, "missing response")
