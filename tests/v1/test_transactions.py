from __future__ import annotations

from typing import Any

import httpx

from nomba.v1.transactions import (
    BankTransaction,
    Transaction,
    Transactions,
    VirtualAccountTransaction,
)


def _bank_tx(tx_id: str) -> dict:
    return {
        "amount": 100.0,
        "currency": "NGN",
        "meta": {"transactionId": tx_id},
        "status": "SUCCESS",
        "timeUpdated": "2024-01-01T00:00:00Z",
        "walletBalance": 500.0,
        "transactionType": "CREDIT",
    }


def _tx(tx_id: str) -> dict:
    return {
        "id": tx_id,
        "status": "SUCCESS",
        "amount": 100.0,
        "source": "api",
        "type": "merchant_payment",
        "gatewayMessage": "Approved",
        "timeCreated": "2024-01-01T00:00:00Z",
    }


def _virtual_tx(tx_id: str) -> dict:
    return {
        "id": tx_id,
        "status": "SUCCESS",
        "amount": "100.0",
        "timeCreated": "2024-01-01T00:00:00Z",
    }


def test_list_bank_transactions_returns_page(fake_http):
    page = {"results": [_bank_tx("b1"), _bank_tx("b2")], "cursor": "next-cursor"}
    http = fake_http(lambda req: httpx.Response(200, json={"code": "00", "data": page}))
    transactions = Transactions(http)
    results, cursor = transactions.list_bank_transactions()
    assert isinstance(results[0], BankTransaction)
    assert results[0].meta["transactionId"] == "b1"
    assert cursor == "next-cursor"


def test_iterate_bank_transactions_paginates(fake_http):
    pages = [
        {"results": [_bank_tx("b1")], "cursor": "c2"},
        {"results": [_bank_tx("b2")], "cursor": ""},
    ]
    calls = []

    def answer(req: httpx.Request) -> httpx.Response:
        calls.append(str(req.url))
        return httpx.Response(200, json={"code": "00", "data": pages[len(calls) - 1]})

    http = fake_http(answer)
    transactions = Transactions(http)
    results = list(transactions.iterate_bank_transactions())
    assert [r.meta["transactionId"] for r in results] == ["b1", "b2"]
    assert "cursor=c2" in calls[1]


def test_list_virtual_account_transactions_sends_query(fake_http):
    seen = {}

    def answer(req: httpx.Request) -> httpx.Response:
        seen["url"] = str(req.url)
        page = {"results": [_virtual_tx("v1")], "cursor": ""}
        return httpx.Response(200, json={"code": "00", "data": page})

    http = fake_http(answer)
    transactions = Transactions(http)
    results, cursor = transactions.list_virtual_account_transactions("1234567890")
    assert isinstance(results[0], VirtualAccountTransaction)
    assert results[0].id == "v1"
    assert cursor is None
    assert "virtual_account=1234567890" in seen["url"]


def test_list_parent_transactions_returns_page(fake_http):
    page = {"results": [_tx("t1")], "cursor": "next-cursor"}
    http = fake_http(lambda req: httpx.Response(200, json={"code": "00", "data": page}))
    transactions = Transactions(http)
    results, cursor = transactions.list_parent_transactions()
    assert isinstance(results[0], Transaction)
    assert results[0].id == "t1"
    assert cursor == "next-cursor"


def test_iterate_parent_transactions_paginates(fake_http):
    pages = [
        {"results": [_tx("t1")], "cursor": "c2"},
        {"results": [_tx("t2")], "cursor": ""},
    ]
    calls = []

    def answer(req: httpx.Request) -> httpx.Response:
        calls.append(str(req.url))
        return httpx.Response(200, json={"code": "00", "data": pages[len(calls) - 1]})

    http = fake_http(answer)
    transactions = Transactions(http)
    results = list(transactions.iterate_parent_transactions())
    assert [r.id for r in results] == ["t1", "t2"]
    assert "cursor=c2" in calls[1]


def test_list_sub_account_transactions_returns_page(fake_http):
    seen = {}

    def answer(req: httpx.Request) -> httpx.Response:
        seen["url"] = str(req.url)
        page = {"results": [_tx("t1")], "cursor": ""}
        return httpx.Response(200, json={"code": "00", "data": page})

    http = fake_http(answer)
    transactions = Transactions(http)
    results, cursor = transactions.list_sub_account_transactions("acc_2")
    assert results[0].id == "t1"
    assert cursor is None
    assert "/v1/transactions/accounts/acc_2" in seen["url"]


def test_iterate_sub_account_transactions_paginates(fake_http):
    page = {"results": [_tx("t1")], "cursor": ""}
    http = fake_http(lambda req: httpx.Response(200, json={"code": "00", "data": page}))
    transactions = Transactions(http)
    results = list(transactions.iterate_sub_account_transactions("acc_2"))
    assert [r.id for r in results] == ["t1"]


def test_filter_parent_transactions_sends_body_and_query(fake_http):
    seen: dict[str, Any] = {}

    def answer(req: httpx.Request) -> httpx.Response:
        seen["url"] = str(req.url)
        seen["body"] = req.read()
        page = {"results": [_tx("t1")], "cursor": ""}
        return httpx.Response(200, json={"code": "00", "data": page})

    http = fake_http(answer)
    transactions = Transactions(http)
    results, _cursor = transactions.filter_parent_transactions(
        filter={"status": "SUCCESS"}, limit=10
    )
    assert results[0].id == "t1"
    assert "limit=10" in seen["url"]
    assert (
        b'"status":"SUCCESS"' in seen["body"] or b'"status": "SUCCESS"' in seen["body"]
    )


def test_iterate_filtered_parent_transactions_paginates(fake_http):
    pages = [
        {"results": [_tx("t1")], "cursor": "c2"},
        {"results": [_tx("t2")], "cursor": ""},
    ]
    calls = []

    def answer(req: httpx.Request) -> httpx.Response:
        calls.append(str(req.url))
        return httpx.Response(200, json={"code": "00", "data": pages[len(calls) - 1]})

    http = fake_http(answer)
    transactions = Transactions(http)
    results = list(
        transactions.iterate_filtered_parent_transactions(filter={"status": "SUCCESS"})
    )
    assert [r.id for r in results] == ["t1", "t2"]
    assert "cursor=c2" in calls[1]


def test_filter_sub_account_transactions_sends_body_and_path(fake_http):
    seen = {}

    def answer(req: httpx.Request) -> httpx.Response:
        seen["url"] = str(req.url)
        page = {"results": [_tx("t1")], "cursor": ""}
        return httpx.Response(200, json={"code": "00", "data": page})

    http = fake_http(answer)
    transactions = Transactions(http)
    results, _cursor = transactions.filter_sub_account_transactions(
        "acc_2", filter={"status": "SUCCESS"}
    )
    assert results[0].id == "t1"
    assert "/v1/transactions/accounts/acc_2" in seen["url"]


def test_iterate_filtered_sub_account_transactions_paginates(fake_http):
    page = {"results": [_tx("t1")], "cursor": ""}
    http = fake_http(lambda req: httpx.Response(200, json={"code": "00", "data": page}))
    transactions = Transactions(http)
    results = list(
        transactions.iterate_filtered_sub_account_transactions(
            "acc_2", filter={"status": "SUCCESS"}
        )
    )
    assert [r.id for r in results] == ["t1"]
