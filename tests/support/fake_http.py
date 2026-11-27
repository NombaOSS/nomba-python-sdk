from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from nomba.http import HttpClient
from nomba.lib.token_store import MemoryTokenStore


def make_fake_http(answer: Callable[[httpx.Request], httpx.Response]) -> HttpClient:
    """Builds an HttpClient wired to answer(request) via httpx.MockTransport.

    Pre-seeds the token store with a valid, non-expiring token so tests don't
    have to simulate the token-issue call unless they are specifically testing
    auth (401/refresh behavior).
    """
    store = MemoryTokenStore()
    expires = datetime.now(UTC) + timedelta(hours=1)
    store.set(
        {
            "businessId": "biz",
            "access_token": "fake-access-token",
            "refresh_token": "fake-refresh-token",
            "expiresAt": expires.isoformat(),
        }
    )
    return HttpClient(
        client_id="dummy-client-id",
        client_secret="dummy-client-secret",
        account_id="dummy-account-id",
        environment="sandbox",
        token_store=store,
        retry_delay_s=0,
        transport=httpx.MockTransport(answer),
    )


@pytest.fixture
def fake_http() -> Callable[[Callable[[httpx.Request], httpx.Response]], HttpClient]:
    return make_fake_http
