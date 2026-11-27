from __future__ import annotations

import httpx

from nomba.v1.accounts import AccountBalance, AccountDetails, Accounts

ACCOUNT_DETAILS = {
    "createdAt": "2024-01-01T00:00:00Z",
    "accountId": "acc_1",
    "accountHolderId": "holder_1",
    "accountRef": "ref_1",
    "bvn": "12345678901",
    "status": "ACTIVE",
    "type": "virtual",
    "accountName": "Jane Doe",
    "currency": "NGN",
    "banks": [
        {
            "bankAccountNumber": "0000000000",
            "bankName": "Nomba",
            "bankAccountName": "Jane Doe",
        }
    ],
}

BALANCE = {
    "amount": "281946.0",
    "currency": "NGN",
    "timeCreated": "2024-01-01T00:00:00Z",
}


def _terminal(terminal_id: str) -> dict:
    return {
        "terminalId": terminal_id,
        "serialNumber": "sn-1",
        "accountId": "acc_1",
        "parentAccountId": "acc_0",
        "merchantName": "Jane Doe",
        "terminalLabel": "Front desk",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
    }


def test_get_parent_account(fake_http):
    http = fake_http(
        lambda req: httpx.Response(200, json={"code": "00", "data": ACCOUNT_DETAILS})
    )
    accounts = Accounts(http)
    account = accounts.get_parent_account()
    assert isinstance(account, AccountDetails)
    assert account.accountId == "acc_1"
    assert account.banks[0]["bankName"] == "Nomba"


def test_get_parent_balance(fake_http):
    http = fake_http(
        lambda req: httpx.Response(200, json={"code": "00", "data": BALANCE})
    )
    accounts = Accounts(http)
    balance = accounts.get_parent_balance()
    assert isinstance(balance, AccountBalance)
    assert balance.amount == "281946.0"


def test_get_sub_account_sends_lookup_query(fake_http):
    seen = {}

    def answer(req: httpx.Request) -> httpx.Response:
        seen["url"] = str(req.url)
        return httpx.Response(200, json={"code": "00", "data": ACCOUNT_DETAILS})

    http = fake_http(answer)
    accounts = Accounts(http)
    account = accounts.get_sub_account(account_id="acc_2")
    assert account.accountId == "acc_1"
    assert "accountId=acc_2" in seen["url"]


def test_get_sub_account_balance(fake_http):
    http = fake_http(
        lambda req: httpx.Response(200, json={"code": "00", "data": BALANCE})
    )
    accounts = Accounts(http)
    balance = accounts.get_sub_account_balance("acc_2")
    assert isinstance(balance, AccountBalance)


def test_list_parent_terminals_returns_page(fake_http):
    page = {"results": [_terminal("t1"), _terminal("t2")], "cursor": "next-cursor"}
    http = fake_http(lambda req: httpx.Response(200, json={"code": "00", "data": page}))
    accounts = Accounts(http)
    terminals, cursor = accounts.list_parent_terminals()
    assert [t.terminalId for t in terminals] == ["t1", "t2"]
    assert cursor == "next-cursor"


def test_iterate_parent_terminals_paginates(fake_http):
    pages = [
        {"results": [_terminal("t1")], "cursor": "c2"},
        {"results": [_terminal("t2")], "cursor": ""},
    ]
    calls = []

    def answer(req: httpx.Request) -> httpx.Response:
        calls.append(str(req.url))
        return httpx.Response(200, json={"code": "00", "data": pages[len(calls) - 1]})

    http = fake_http(answer)
    accounts = Accounts(http)
    terminals = list(accounts.iterate_parent_terminals())
    assert [t.terminalId for t in terminals] == ["t1", "t2"]
    assert "cursor=c2" in calls[1]


def test_iterate_sub_account_terminals_paginates(fake_http):
    pages = [
        {"results": [_terminal("t1")], "cursor": ""},
    ]
    http = fake_http(
        lambda req: httpx.Response(200, json={"code": "00", "data": pages[0]})
    )
    accounts = Accounts(http)
    terminals = list(accounts.iterate_sub_account_terminals("acc_2"))
    assert [t.terminalId for t in terminals] == ["t1"]
