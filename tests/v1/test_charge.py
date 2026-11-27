from __future__ import annotations

import httpx

from nomba.v1.charge import Charge


def test_get_order(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {"order": {"orderReference": "ord1"}, "hasSavedCards": True},
            },
        )

    http = fake_http(handler)
    charge = Charge(http)
    result = charge.get_order("ord1")
    assert result.hasSavedCards is True
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v1/checkout/order/ord1"


def test_submit_card_details_stringifies_dict_card_details(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {"status": True, "responseCode": "T0", "transactionId": "tx1"},
            },
        )

    http = fake_http(handler)
    charge = Charge(http)
    result = charge.submit_card_details(
        orderReference="ord1",
        cardDetails={
            "cardNumber": "4111",
            "cardCVV": "123",
            "cardExpiryMonth": "01",
            "cardExpiryYear": "30",
            "cardPin": "1234",
        },
    )
    assert result.responseCode == "T0"
    assert result.transactionId == "tx1"
    import json

    body = json.loads(captured["request"].content)
    assert isinstance(body["cardDetails"], str)


def test_submit_card_otp(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"status": True, "message": "ok"}}
        )
    )
    charge = Charge(http)
    result = charge.submit_card_otp("1234", "ord1", "tx1")
    assert result.status is True


def test_resend_otp(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"success": True, "message": "sent"}}
        )
    )
    charge = Charge(http)
    result = charge.resend_otp("ord1")
    assert result.success is True


def test_fetch_transaction_details(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200, json={"code": "00", "data": {"status": True, "message": "ok"}}
        )

    http = fake_http(handler)
    charge = Charge(http)
    result = charge.fetch_transaction_details("ord1")
    assert result.status is True
    req = captured["request"]
    assert req.url.path == "/v1/checkout/confirm-transaction-receipt"


def test_fetch_flash_account(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200,
            json={
                "code": "00",
                "data": {
                    "accountNumber": "123",
                    "accountName": "Jane",
                    "bankName": "Flash",
                },
            },
        )
    )
    charge = Charge(http)
    result = charge.fetch_flash_account("ord1")
    assert result.accountNumber == "123"


def test_cancel_transaction(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"success": True, "message": "cancelled"}}
        )
    )
    charge = Charge(http)
    result = charge.cancel_transaction("tx1", True)
    assert result.success is True


def test_request_saved_cards_otp(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"success": True, "message": "sent"}}
        )
    )
    charge = Charge(http)
    result = charge.request_saved_cards_otp("ord1")
    assert result.success is True


def test_get_saved_cards(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {
                    "tokenizedCardData": [{"tokenKey": "tk1", "cardType": "visa"}]
                },
            },
        )

    http = fake_http(handler)
    charge = Charge(http)
    cards = charge.get_saved_cards("ord1", "1234")
    assert cards[0].tokenKey == "tk1"
    req = captured["request"]
    assert req.url.path == "/v1/checkout/user-card/ord1"
    assert "otp=1234" in str(req.url)


def test_request_save_card_otp(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"success": True, "message": "sent"}}
        )
    )
    charge = Charge(http)
    result = charge.request_save_card_otp("ord1", "08012345678")
    assert result.success is True


def test_submit_save_card_otp(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"success": True, "message": "saved"}}
        )
    )
    charge = Charge(http)
    result = charge.submit_save_card_otp("ord1", "08012345678", "1234")
    assert result.success is True
