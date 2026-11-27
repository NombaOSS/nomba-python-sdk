from __future__ import annotations

import httpx
import pytest

from nomba.lib.errors import NombaError, UnconfirmedOutcomeError
from nomba.v1.accounts import Terminal as AccountsTerminal
from nomba.v1.terminals import Terminal, Terminals


def _terminal(terminal_id: str) -> dict:
    return {
        "terminalId": terminal_id,
        "serialNumber": "SN1",
        "accountId": "acc1",
        "parentAccountId": "parent1",
        "merchantName": "Merchant",
        "terminalLabel": "Front Desk",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
    }


def test_terminal_is_shared_between_accounts_and_terminals_modules():
    # Per Task 10's mandatory move: Terminal now canonically lives in nomba.terminals,
    # and nomba.accounts re-imports it rather than defining its own copy.
    assert AccountsTerminal is Terminal


def test_assign_to_parent(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": _terminal("t1")})

    http = fake_http(handler)
    terminals = Terminals(http)
    result = terminals.assign_to_parent(serialNumber="SN1")
    assert isinstance(result, Terminal)
    assert result.terminalId == "t1"
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v1/terminals/assign"


def test_assign_to_sub_account(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": _terminal("t2")})

    http = fake_http(handler)
    terminals = Terminals(http)
    result = terminals.assign_to_sub_account("sub1", serialNumber="SN1")
    assert isinstance(result, Terminal)
    req = captured["request"]
    assert req.url.path == "/v1/terminals/assign/sub1"


def test_unassign_from_parent(fake_http):
    http = fake_http(
        lambda req: httpx.Response(200, json={"code": "00", "data": _terminal("t3")})
    )
    terminals = Terminals(http)
    result = terminals.unassign_from_parent(serialNumber="SN1")
    assert isinstance(result, Terminal)


def test_unassign_from_sub_account(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": _terminal("t4")})

    http = fake_http(handler)
    terminals = Terminals(http)
    result = terminals.unassign_from_sub_account("sub2", serialNumber="SN1")
    assert isinstance(result, Terminal)
    req = captured["request"]
    assert req.url.path == "/v1/terminals/unassign/sub2"


def test_push_payment_request_success(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {
                    "paymentId": "p1",
                    "status": "completed",
                    "amount": 100,
                    "currency": "NGN",
                    "createdAt": "2024-01-01T00:00:00Z",
                },
            },
        )

    http = fake_http(handler)
    terminals = Terminals(http)
    result = terminals.push_payment_request("term1", "ref1", 100, "NGN")
    assert result["status"] == "completed"
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v1/terminals/payment-request/term1"


def test_push_payment_request_pending_raises_without_handler(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"status": "pending"}}
        )
    )
    terminals = Terminals(http)
    with pytest.raises(UnconfirmedOutcomeError):
        terminals.push_payment_request("term1", "ref1", 100, "NGN")


def test_push_payment_request_pending_calls_on_pending(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"status": "pending"}}
        )
    )
    terminals = Terminals(http)
    result = terminals.push_payment_request(
        "term1", "ref1", 100, "NGN", on_pending=lambda data: "handled"
    )
    assert result == "handled"


def test_push_payment_request_rejected_code_raises_nomba_error(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            400, json={"code": "400", "description": "bad request"}
        )
    )
    terminals = Terminals(http)
    with pytest.raises(NombaError):
        terminals.push_payment_request("term1", "ref1", 100, "NGN")
