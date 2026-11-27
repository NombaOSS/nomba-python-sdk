import httpx
import pytest

from nomba.lib.errors import (
    IdempotencyKeyAbsentError,
    NombaError,
    OutcomeUnknownError,
    UnconfirmedOutcomeError,
)
from nomba.lib.outcome import (
    REJECTED,
    FailedInfo,
    OutcomeTable,
    PendingInfo,
    classify,
    settle,
)

TABLE = OutcomeTable(
    codes={"00": "success", "200": "success", "201": "pending", **REJECTED},
    statuses={"SUCCESS": "success", "PENDING_BILLING": "pending"},
)


def _settle(http, **kw):
    return settle(
        http, "POST", "/p", TABLE, field="merchantTxRef", key="k1", body={}, **kw
    )


def _reply(status, payload):
    return lambda req: httpx.Response(status, json=payload)


def test_classify():
    assert classify(TABLE, "200", "SUCCESS") == "success"
    assert classify(TABLE, "201", "SUCCESS") == "pending"
    assert classify(TABLE, "00", "REFUND") == "pending"
    assert classify(TABLE, "00", None) == "pending"
    assert classify(TABLE, "99", "SUCCESS") == "pending"


@pytest.mark.parametrize("key", [None, "", "   "])
def test_missing_key_raises_before_any_request(fake_http, key):
    calls = []

    def answer(req):
        calls.append(req)
        return httpx.Response(200)

    http = fake_http(answer)
    with pytest.raises(IdempotencyKeyAbsentError) as e:
        settle(http, "POST", "/p", TABLE, field="merchantTxRef", key=key)
    assert e.value.field == "merchantTxRef"
    assert calls == []


@pytest.mark.parametrize("code", ["00", "200"])
def test_success_codes(fake_http, code):
    http = fake_http(_reply(200, {"code": code, "data": {"status": "SUCCESS"}}))
    assert _settle(http) == {"status": "SUCCESS"}
    assert _settle(http, on_success=lambda d: "ok") == "ok"


def test_pending_code_hands_data_to_on_pending(fake_http):
    http = fake_http(
        _reply(200, {"code": "201", "data": {"status": "PENDING_BILLING"}})
    )
    info = _settle(http, on_pending=lambda i: i)
    assert info == PendingInfo(
        data={"status": "PENDING_BILLING"},
        code="201",
        status="PENDING_BILLING",
        idempotency_key="k1",
    )
    with pytest.raises(UnconfirmedOutcomeError) as e:
        _settle(http)
    assert (e.value.reason, e.value.code, e.value.idempotency_key) == (
        "code",
        "201",
        "k1",
    )


def test_undocumented_status_is_pending(fake_http):
    http = fake_http(_reply(200, {"code": "00", "data": {"status": "REFUND"}}))
    with pytest.raises(UnconfirmedOutcomeError) as e:
        _settle(http)
    assert (e.value.reason, e.value.status) == ("status", "REFUND")


def test_rejection_by_http_status_is_failed(fake_http):
    http = fake_http(_reply(400, {"code": "VALIDATION_ERROR", "description": "bad"}))
    info = _settle(http, on_failed=lambda i: i)
    assert isinstance(info, FailedInfo) and info.code == "VALIDATION_ERROR"
    with pytest.raises(NombaError):
        _settle(http)


def test_undocumented_code_on_2xx_is_pending_not_failed(fake_http):
    http = fake_http(_reply(200, {"code": "77", "data": {}}))
    with pytest.raises(UnconfirmedOutcomeError):
        _settle(http)


def test_transport_failure_is_pending(fake_http):
    def boom(req):
        raise httpx.ReadTimeout("slow")

    http = fake_http(boom)
    info = _settle(http, on_pending=lambda i: i)
    assert isinstance(info.cause, OutcomeUnknownError) and info.idempotency_key == "k1"
    with pytest.raises(OutcomeUnknownError):
        _settle(http)


def test_on_outcome_hook_reports_every_call(fake_http):
    events: list[dict] = []
    http = fake_http(_reply(200, {"code": "200", "data": {"status": "SUCCESS"}}))
    http._on_outcome = events.append
    _settle(http)
    assert events == [
        {
            "method": "POST",
            "path": "/p",
            "outcome": "success",
            "code": "200",
            "status": "SUCCESS",
            "idempotency_key": "k1",
        }
    ]
