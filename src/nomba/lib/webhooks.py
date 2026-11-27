"""Webhook signature verification, for use in a webhook receiver.

Ported from Node's ``src/lib/webhooks.ts``. The signing string the docs define is:
``event_type:requestId:userId:walletId:transactionId:type:time:responseCode:timestamp``
with a missing field (or a ``responseCode`` of ``"null"``) treated as ``""``. The signature
is the base64 HMAC-SHA256 of that string, compared exactly (case-sensitive) and in
constant time.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any


def _signing_string(event: dict[str, Any], timestamp: str) -> str | None:
    """The colon-joined message Nomba signs, or ``None`` if `event` is missing a field the
    signature depends on. A field is never defaulted to ``""`` silently: that would let a
    malformed body verify against a signature computed over different, unintended data."""
    event_type = event.get("event_type")
    request_id = event.get("requestId")
    data = event.get("data")
    if not isinstance(event_type, str) or not event_type:
        return None
    if not isinstance(request_id, str) or not request_id:
        return None
    if not isinstance(data, dict):
        return None
    merchant = data.get("merchant")
    tx = data.get("transaction")
    if not isinstance(merchant, dict) or not isinstance(tx, dict):
        return None
    response_code = tx.get("responseCode")
    response_code = "" if response_code in (None, "null") else str(response_code)
    if ":" in response_code:
        # The signed string is colon-joined and the timestamp itself contains colons, so a
        # responseCode containing ":" could shift a later field into an earlier one without
        # changing the signature.
        return None
    fields = [
        event_type,
        request_id,
        merchant.get("userId"),
        merchant.get("walletId"),
        tx.get("transactionId"),
        tx.get("type"),
        tx.get("time"),
        response_code,
        timestamp,
    ]
    return ":".join(str(f) if f else "" for f in fields)


def verify_signature(
    body: str | bytes | dict[str, Any],
    signature: str | None,
    timestamp: str,
    secret: str,
) -> bool:
    """True when `signature` (the nomba-signature header) matches `body`, signed with the
    dashboard's webhook signature key and the nomba-timestamp header. `body` is the raw
    request body (str/bytes) or the already-parsed event. Never raises: a missing or
    malformed signature or body returns False.
    """
    if not isinstance(signature, str) or not signature:
        return False

    if isinstance(body, (str, bytes)):
        try:
            event = json.loads(body)
        except (ValueError, TypeError):
            return False
    else:
        event = body
    if not isinstance(event, dict):
        return False

    signed = _signing_string(event, timestamp)
    if signed is None:
        return False
    digest = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    # Exact, constant-time comparison. Base64 is case-sensitive, so comparing
    # case-insensitively would accept signatures Nomba never produced. Compared as bytes:
    # hmac.compare_digest raises TypeError on a str containing non-ASCII characters, and
    # `signature` comes straight from an attacker-controlled header.
    return hmac.compare_digest(expected.encode(), signature.encode())
