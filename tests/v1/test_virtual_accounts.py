from __future__ import annotations

import httpx

from nomba.v1.virtual_accounts import (
    CreatedVirtualAccount,
    VirtualAccount,
    VirtualAccounts,
)


def _va(ref: str) -> dict:
    return {
        "createdAt": "2024-01-01T00:00:00Z",
        "accountHolderId": "ah1",
        "accountRef": ref,
        "bvn": "12345678901",
        "accountName": "Test Account",
        "bankName": "Nomba MFB",
        "bankAccountName": "Test Account",
        "bankAccountNumber": "1234567890",
        "currency": "NGN",
        "expired": False,
    }


def test_create_returns_created_virtual_account(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": _va("ref1")})

    http = fake_http(handler)
    va = VirtualAccounts(http)
    result = va.create(accountRef="ref1", accountName="Test Account")
    assert isinstance(result, CreatedVirtualAccount)
    assert result.accountRef == "ref1"
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v1/accounts/virtual"


def test_create_for_sub_account(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": _va("ref2")})

    http = fake_http(handler)
    va = VirtualAccounts(http)
    result = va.create_for_sub_account("sub1", accountRef="ref2", accountName="Test")
    assert isinstance(result, CreatedVirtualAccount)
    req = captured["request"]
    assert req.url.path == "/v1/accounts/virtual/sub1"


def test_get_returns_virtual_account(fake_http):
    http = fake_http(
        lambda req: httpx.Response(200, json={"code": "00", "data": _va("ref3")})
    )
    va = VirtualAccounts(http)
    result = va.get("ref3")
    assert isinstance(result, VirtualAccount)
    assert result.bankAccountNumber == "1234567890"


def test_get_filters_unknown_keys(fake_http):
    data = _va("ref4")
    data["someNewField"] = "unexpected"
    http = fake_http(lambda req: httpx.Response(200, json={"code": "00", "data": data}))
    va = VirtualAccounts(http)
    result = va.get("ref4")
    assert isinstance(result, VirtualAccount)
    assert result.accountRef == "ref4"


def test_update(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": {"updated": True}})

    http = fake_http(handler)
    va = VirtualAccounts(http)
    result = va.update("ref5", accountName="New Name")
    assert result == {"updated": True}
    req = captured["request"]
    assert req.method == "PUT"
    assert req.url.path == "/v1/accounts/virtual/ref5"


def test_expire(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": {"expired": True}})

    http = fake_http(handler)
    va = VirtualAccounts(http)
    result = va.expire("ref6")
    assert result == {"expired": True}
    req = captured["request"]
    assert req.method == "DELETE"
    assert req.url.path == "/v1/accounts/virtual/ref6"


def test_list_returns_page(fake_http):
    page = {"results": [_va("ref7"), _va("ref8")], "cursor": "next-cursor"}
    http = fake_http(lambda req: httpx.Response(200, json={"code": "00", "data": page}))
    va = VirtualAccounts(http)
    results, cursor = va.list()
    assert len(results) == 2
    assert isinstance(results[0], VirtualAccount)
    assert cursor == "next-cursor"


def test_iterate_paginates(fake_http):
    pages = [
        {"results": [_va("ref9")], "cursor": "c2"},
        {"results": [_va("ref10")], "cursor": ""},
    ]
    calls = {"n": 0}

    def handler(req):
        page = pages[calls["n"]]
        calls["n"] += 1
        return httpx.Response(200, json={"code": "00", "data": page})

    http = fake_http(handler)
    va = VirtualAccounts(http)
    results = list(va.iterate())
    assert [r.accountRef for r in results] == ["ref9", "ref10"]
