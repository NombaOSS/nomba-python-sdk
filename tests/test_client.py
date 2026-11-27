from __future__ import annotations

from nomba.client import Nomba
from nomba.v1.accounts import Accounts


def test_client_exposes_accounts_resource(fake_http):
    http = fake_http(lambda req: None)  # never called
    client = Nomba(client_id="x", client_secret="y", account_id="z", http_client=http)
    assert isinstance(client.accounts, Accounts)
    assert client.accounts._http is http


def test_client_builds_http_client_from_credentials():
    client = Nomba(
        client_id="x", client_secret="y", account_id="z", environment="sandbox"
    )
    assert client._http.environment == "sandbox"
    assert isinstance(client.accounts, Accounts)
