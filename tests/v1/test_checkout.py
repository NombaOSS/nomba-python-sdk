from __future__ import annotations

import httpx
import pytest

from nomba.lib.errors import NombaError, UnconfirmedOutcomeError
from nomba.v1.checkout import Checkout


def test_create_order(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {
                    "checkoutLink": "https://pay.example/x",
                    "orderReference": "ord1",
                },
            },
        )

    http = fake_http(handler)
    checkout = Checkout(http)
    result = checkout.create_order(
        {
            "orderReference": "ord1",
            "callbackUrl": "https://cb",
            "customerEmail": "a@b.com",
            "amount": 100,
            "currency": "NGN",
        }
    )
    assert result.checkoutLink == "https://pay.example/x"
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v1/checkout/order"


def test_fetch_transaction(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={"code": "00", "data": {"success": True, "message": "ok"}},
        )

    http = fake_http(handler)
    checkout = Checkout(http)
    result = checkout.fetch_transaction(idType="ORDER_REFERENCE", id="ord1")
    assert result.success is True
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v1/checkout/transaction"


def test_cancel_order(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"success": True, "message": "cancelled"}}
        )
    )
    checkout = Checkout(http)
    result = checkout.cancel_order("ord1")
    assert result.success is True


def test_charge_tokenized_card(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"status": True, "otpRequired": False}}
        )
    )
    checkout = Checkout(http)
    result = checkout.charge_tokenized_card("tok1")
    assert result.status is True
    assert result.otpRequired is False


def test_list_tokenized_cards(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200,
            json={
                "code": "00",
                "data": {
                    "nextPage": "0",
                    "tokenizedCardDataList": [{"tokenKey": "tk1", "cardType": "visa"}],
                },
            },
        )
    )
    checkout = Checkout(http)
    cards, cursor = checkout.list_tokenized_cards()
    assert cards[0].tokenKey == "tk1"
    assert cursor is None


def test_iterate_tokenized_cards(fake_http):
    pages = [
        {"nextPage": "2", "tokenizedCardDataList": [{"tokenKey": "tk1"}]},
        {"nextPage": "0", "tokenizedCardDataList": [{"tokenKey": "tk2"}]},
    ]

    def handler(req):
        return httpx.Response(200, json={"code": "00", "data": pages.pop(0)})

    http = fake_http(handler)
    checkout = Checkout(http)
    cards = list(checkout.iterate_tokenized_cards())
    assert [c.tokenKey for c in cards] == ["tk1", "tk2"]


def test_update_tokenized_card(fake_http):
    http = fake_http(
        lambda req: httpx.Response(200, json={"code": "00", "data": {"status": True}})
    )
    checkout = Checkout(http)
    result = checkout.update_tokenized_card("tok1", "old@x.com", "new@x.com")
    assert result.status is True


def test_delete_tokenized_card(fake_http):
    http = fake_http(
        lambda req: httpx.Response(200, json={"code": "00", "data": {"status": True}})
    )
    checkout = Checkout(http)
    result = checkout.delete_tokenized_card("tok1")
    assert result.status is True


def test_refund_success(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200, json={"code": "00", "data": {"success": True, "message": "ok"}}
        )

    http = fake_http(handler)
    checkout = Checkout(http)
    result = checkout.refund("txn1")
    assert result["success"] is True
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v1/checkout/refund"


def test_refund_pending_raises_without_handler(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"success": False, "message": "not yet"}}
        )
    )
    checkout = Checkout(http)
    with pytest.raises(UnconfirmedOutcomeError):
        checkout.refund("txn1")


def test_refund_pending_calls_on_pending(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"success": False, "message": "not yet"}}
        )
    )
    checkout = Checkout(http)
    result = checkout.refund("txn1", on_pending=lambda data: "handled")
    assert result == "handled"


def test_refund_undocumented_status_raises_without_handler(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"message": "no success flag"}}
        )
    )
    checkout = Checkout(http)
    with pytest.raises(UnconfirmedOutcomeError):
        checkout.refund("txn1")


def test_refund_rejected_code_raises_nomba_error(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            400, json={"code": "400", "description": "bad request"}
        )
    )
    checkout = Checkout(http)
    with pytest.raises(NombaError):
        checkout.refund("txn1")
