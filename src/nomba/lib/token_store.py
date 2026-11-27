"""Where the SDK keeps its access token, ported from the Node SDK's ``src/lib/token-store.ts``."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Protocol, TypedDict, TypeVar

T = TypeVar("T")


class TokenData(TypedDict):
    """The ``data`` of ``POST /v1/auth/token/issue`` and ``/refresh``."""

    businessId: str
    access_token: str
    refresh_token: str
    expiresAt: str  # ISO 8601 UTC, e.g. 2022-07-08T14:33:00Z


class TokenStore(Protocol):
    """Implement over Redis, a database, etc. so several instances share one token.

    - ``get``/``set``/``clear`` must be atomic and durable.
    - Nomba allows a single session per client, so a shared store should also define
      ``lock(fn)``: run ``fn`` while holding a cross-instance lock (with a TTL) and return
      its result. The SDK runs every issue/refresh/revoke inside it.
    - Store errors never fail a request: ``set`` is retried twice, then the token is kept in
      process memory and the error is passed to ``on_store_error``.
    """

    def get(self) -> TokenData | None: ...
    def set(self, token: TokenData) -> None: ...
    def clear(self) -> None: ...


class MemoryTokenStore:
    """Default store: one token, this process only."""

    def __init__(self) -> None:
        self._token: TokenData | None = None

    def get(self) -> TokenData | None:
        return self._token

    def set(self, token: TokenData) -> None:
        self._token = token

    def clear(self) -> None:
        self._token = None


def run_locked[T](store: TokenStore, fn: Callable[[], T], local: threading.Lock) -> T:
    """Run ``fn`` under the process-local lock and, if the store defines one, its
    cross-instance ``lock``."""
    with local:
        lock = getattr(store, "lock", None)
        return lock(fn) if callable(lock) else fn()
