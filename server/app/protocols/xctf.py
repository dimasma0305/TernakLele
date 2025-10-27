import requests
import logging
from typing import Iterable, Dict, Any

from models import FlagStatus, SubmitResult

logger = logging.getLogger(__name__)

API_TIMEOUT = 10
# Rate limit: 10 TPS according to documentation
# We'll submit flags sequentially to respect rate limits


def submit_flags(flags: Iterable[Any], config: Dict[str, str]):
    """
    Submit flags to XCTF API.
    
    Args:
        flags: iterable objects with `.flag` attribute
        config: must contain:
            - SYSTEM_URL: base URL (e.g., http://10.2.65.1)
            - SYSTEM_TOKEN: team token
            - RACE_ID: race ID (e.g., b2a01b4b88df2f76b05bbc1e4e50b2f7)
    Yields:
        SubmitResult for each flag
    """
    
    base_url = config['SYSTEM_URL'].rstrip('/')
    token = config['SYSTEM_TOKEN']
    race_id = config.get('RACE_ID', 'b2a01b4b88df2f76b05bbc1e4e50b2f7')
    
    url = f"{base_url}/api/ct/web/awd_race/race/{race_id}/flag/robot/"
    headers = {
        "Content-Type": "application/json",
    }
    
    sess = requests.Session()
    
    flags_list = list(flags)
    
    for flag_obj in flags_list:
        payload = {
            "flag": flag_obj.flag,
            "token": token
        }
        
        try:
            r = sess.post(url, json=payload, headers=headers, timeout=API_TIMEOUT)
        except requests.RequestException as e:
            logger.error("HTTP request error for flag %s: %s", flag_obj.flag, e)
            yield SubmitResult(flag_obj.flag, FlagStatus.QUEUED, str(e))
            continue
        
        # Parse response
        try:
            resp = r.json()
        except ValueError:
            logger.error("Invalid JSON response for flag %s: %s", flag_obj.flag, r.text)
            yield SubmitResult(flag_obj.flag, FlagStatus.QUEUED, f"Invalid JSON: {r.text[:100]}")
            continue
        
        # Check response code
        code = resp.get("code", "")
        message = resp.get("message", "")
        data = resp.get("data", {})
        
        # Determine status based on response
        if code.startswith("AD-000000") or (isinstance(data, dict) and data.get("is_pass")):
            # Flag accepted
            is_duplicate = data.get("is_duplicate", False)
            if is_duplicate:
                status = FlagStatus.REJECTED
                response_msg = "Flag already submitted (duplicate)"
            else:
                status = FlagStatus.ACCEPTED
                response_msg = "Flag accepted"
        elif code:
            # Some error code returned
            # Check if it's a temporary error (should retry) or permanent rejection
            code_lower = code.lower()
            message_lower = message.lower() if message else ""
            
            if any(keyword in message_lower for keyword in ['timeout', 'busy', 'rate limit', 'try again']):
                status = FlagStatus.QUEUED
                response_msg = f"Temporary error: {code} - {message}"
            elif any(keyword in message_lower for keyword in ['wrong', 'invalid', 'expired', 'not found']):
                status = FlagStatus.REJECTED
                response_msg = f"Rejected: {code} - {message}"
            else:
                # Unknown error, queue for retry
                status = FlagStatus.QUEUED
                response_msg = f"Unknown response: {code} - {message}"
        else:
            # No code in response, unexpected format
            logger.warning("Unexpected response format for flag %s: %s", flag_obj.flag, resp)
            status = FlagStatus.QUEUED
            response_msg = f"Unexpected format: {resp}"
        
        yield SubmitResult(flag_obj.flag, status, response_msg)

