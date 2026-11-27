from __future__ import annotations

import base64
import hashlib
import hmac
import json

from nomba.lib.webhooks import verify_signature

SECRET = "whsec_test"
TIMESTAMP = "1700000000"


def _event(
    event_type="payment_success",
    request_id="req-1",
    user_id="user-1",
    wallet_id="wallet-1",
    transaction_id="tx-1",
    tx_type="payment",
    time="2026-10-20T00:00:00Z",
    response_code="00",
):
    return {
        "event_type": event_type,
        "requestId": request_id,
        "data": {
            "merchant": {"userId": user_id, "walletId": wallet_id},
            "transaction": {
                "transactionId": transaction_id,
                "type": tx_type,
                "time": time,
                "responseCode": response_code,
            },
        },
    }


def _sign(event: dict, timestamp: str, secret: str) -> str:
    merchant = event["data"]["merchant"]
    tx = event["data"]["transaction"]
    response_code = tx["responseCode"]
    if response_code == "null":
        response_code = ""
    fields = [
        event["event_type"],
        event["requestId"],
        merchant["userId"],
        merchant["walletId"],
        tx["transactionId"],
        tx["type"],
        tx["time"],
        response_code,
        timestamp,
    ]
    signed = ":".join(str(f) if f else "" for f in fields)
    digest = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def test_verify_signature_true_for_correct_hmac():
    event = _event()
    sig = _sign(event, TIMESTAMP, SECRET)
    assert verify_signature(json.dumps(event), sig, TIMESTAMP, SECRET) is True


def test_verify_signature_true_for_parsed_dict_body():
    event = _event()
    sig = _sign(event, TIMESTAMP, SECRET)
    assert verify_signature(event, sig, TIMESTAMP, SECRET) is True


def test_verify_signature_false_for_wrong_case_signature():
    # Base64 is case-sensitive: a signature that differs only in letter case was never
    # produced by Nomba and must not verify.
    event = _event()
    sig = _sign(event, TIMESTAMP, SECRET)
    assert (
        verify_signature(json.dumps(event), sig.swapcase(), TIMESTAMP, SECRET) is False
    )


def test_verify_signature_false_for_wrong_secret():
    event = _event()
    sig = _sign(event, TIMESTAMP, SECRET)
    assert verify_signature(json.dumps(event), sig, TIMESTAMP, "wrong-secret") is False


def test_verify_signature_false_for_tampered_body():
    event = _event()
    sig = _sign(event, TIMESTAMP, SECRET)
    tampered = _event(transaction_id="tx-2")
    assert verify_signature(json.dumps(tampered), sig, TIMESTAMP, SECRET) is False


def test_verify_signature_null_response_code_treated_as_empty():
    event = _event(response_code="null")
    sig = _sign(event, TIMESTAMP, SECRET)
    assert verify_signature(json.dumps(event), sig, TIMESTAMP, SECRET) is True


def test_verify_signature_returns_false_for_malformed_json_body():
    assert verify_signature("not-json", "deadbeef", TIMESTAMP, SECRET) is False


def test_verify_signature_returns_false_for_empty_body():
    assert verify_signature("", "deadbeef", TIMESTAMP, SECRET) is False


def test_verify_signature_returns_false_for_missing_signature():
    event = _event()
    assert verify_signature(json.dumps(event), None, TIMESTAMP, SECRET) is False


def test_verify_signature_returns_false_for_empty_signature():
    event = _event()
    assert verify_signature(json.dumps(event), "", TIMESTAMP, SECRET) is False


def test_verify_signature_returns_false_for_non_dict_body():
    assert (
        verify_signature(json.dumps([1, 2, 3]), "deadbeef", TIMESTAMP, SECRET) is False
    )


def test_verify_signature_rejects_colon_in_response_code():
    # A ":" in responseCode could shift a later signed field across a boundary without
    # changing the signature, so it must never verify, even against a correctly computed one.
    event = _event(response_code="00:extra")
    sig = _sign(event, TIMESTAMP, SECRET)
    assert verify_signature(json.dumps(event), sig, TIMESTAMP, SECRET) is False


def test_verify_signature_returns_false_for_non_ascii_signature():
    # hmac.compare_digest raises TypeError on a str with non-ASCII characters; the signature
    # header is attacker-controlled, so this must return False, not raise.
    event = _event()
    assert verify_signature(json.dumps(event), "é" * 8, TIMESTAMP, SECRET) is False


def test_verify_signature_returns_false_for_missing_data_object():
    event = {"event_type": "payment_success", "requestId": "req-1"}
    assert verify_signature(json.dumps(event), "deadbeef", TIMESTAMP, SECRET) is False


def test_verify_signature_returns_false_for_missing_merchant_or_transaction():
    event = {"event_type": "payment_success", "requestId": "req-1", "data": {}}
    assert verify_signature(json.dumps(event), "deadbeef", TIMESTAMP, SECRET) is False
