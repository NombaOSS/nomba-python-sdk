"""Authenticated HTTP transport: token lifecycle, retries, response envelope.

Ported from the Node SDK's ``src/services/http/http-client.service.ts``.
"""

from __future__ import annotations

import logging
import random
import re
import threading
import time
import uuid
from collections.abc import Callable, Mapping
from datetime import datetime
from email.utils import parsedate_to_datetime
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Literal

import httpx

from nomba.lib.errors import NombaError, OutcomeUnknownError, TokenError, build_error
from nomba.lib.token_store import MemoryTokenStore, TokenData, TokenStore, run_locked

log = logging.getLogger("nomba")

try:
    SDK_VERSION = version("nomba")
except PackageNotFoundError:  # running from a source tree that is not installed
    SDK_VERSION = "0.0.0"

BASE_URLS: dict[str, str] = {
    "production": "https://api.nomba.com",
    "sandbox": "https://sandbox.nomba.com",
}

# Docs: refresh the access_token at least 5 minutes before it expires.
REFRESH_MARGIN_S = 5 * 60
# A failed store.set() is retried this many times (0.1s, 0.2s apart) before giving up on the shared copy.
SET_RETRIES = 2

Query = Mapping[str, "str | int | float | bool | None"]
Hook = Callable[[dict[str, Any]], None]

# Ported from Node's src/types/common/common.types.ts. The API also accepts lowercase
# values (glo, mtn, ...).
Network = Literal["GLO", "MTN", "9MOBILE", "AIRTEL", "glo", "mtn", "9mobile", "airtel"]


class _UnreadableResponse(Exception):
    """A 2xx whose body could not be read: whether it took effect is unknown."""


def _expires_at(t: TokenData) -> float:
    return datetime.fromisoformat(t["expiresAt"]).timestamp()


def _qs_value(v: str | float | bool) -> str:
    # Match JS String(v): booleans are "true"/"false", not "True"/"False".
    return ("true" if v else "false") if isinstance(v, bool) else str(v)


def _retry_after_seconds(header: str | None) -> float | None:
    """Parse a 429 ``Retry-After`` header: either a delay in seconds or an HTTP-date."""
    if not header:
        return None
    try:
        return max(0.0, float(header))
    except ValueError:
        pass
    try:
        dt = parsedate_to_datetime(header)
        return max(0.0, (dt - datetime.now(dt.tzinfo)).total_seconds())
    except (TypeError, ValueError):
        return None


class HttpClient:
    """Authenticated transport for the Nomba API: owns the token lifecycle (issue, refresh,
    revoke, sharing via ``TokenStore``) and the retry/idempotency rules for ``request``."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        account_id: str,
        environment: str = "production",
        *,
        token_store: TokenStore | None = None,
        on_store_error: Callable[[BaseException], None] | None = None,
        timeout_s: float = 30.0,
        max_attempts: int = 3,
        retry_delay_s: float = 0.5,
        transport: httpx.BaseTransport | None = None,
        on_request: Hook | None = None,
        on_response: Hook | None = None,
        on_outcome: Hook | None = None,
    ) -> None:
        if environment not in BASE_URLS:
            raise ValueError(
                f'Unknown environment "{environment}"; use "production" or "sandbox"'
            )
        self.environment = environment
        self._client_id = client_id
        self._client_secret = client_secret
        self._account_id = account_id
        self._base_url = BASE_URLS[environment]
        self._store: TokenStore = token_store or MemoryTokenStore()
        self._on_store_error = on_store_error or (
            lambda e: log.warning("nomba: token store error: %r", e)
        )
        self._max_attempts = max_attempts
        self._retry_delay_s = retry_delay_s
        self._on_request = on_request
        self._on_response = on_response
        self._on_outcome = on_outcome
        self._client = httpx.Client(transport=transport, timeout=timeout_s)
        # One renewal at a time in this process; the store's lock (if any) covers other instances.
        self._lock = threading.Lock()
        # This process's copy of the latest token, used when the shared store is failing.
        self._local: TokenData | None = None
        # True when the last store.set() failed, so _local is newer than whatever the store holds.
        self._unsynced = False

    # ---- token lifecycle -------------------------------------------------------------

    def issue_token(self) -> TokenData:
        """``POST /v1/auth/token/issue``. Saved to the configured ``TokenStore``."""
        return run_locked(self._store, self._issue, self._lock)

    def refresh_token(self) -> TokenData:
        """``POST /v1/auth/token/refresh``. Raises ``RuntimeError`` if no token is held."""

        def go() -> TokenData:
            t = self._read()
            if t is None:
                raise RuntimeError("No token to refresh; call issue_token() first")
            return self._refresh(t)

        return run_locked(self._store, go, self._lock)

    def revoke_token(self) -> None:
        """``POST /v1/auth/token/revoke``. A no-op if no token is held."""

        def go() -> None:
            t = self._read()
            if t is None:
                return
            self._send(
                "POST",
                "/v1/auth/token/revoke",
                body={"clientId": self._client_id, "access_token": t["access_token"]},
            )
            self._local = None
            self._unsynced = False
            try:
                self._store.clear()
            except Exception as e:  # noqa: BLE001 -- a caller's store may raise anything
                self._on_store_error(e)

        run_locked(self._store, go, self._lock)

    def _issue(self) -> TokenData:
        data = self._send(
            "POST",
            "/v1/auth/token/issue",
            body={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        return self._save(data)

    def _refresh(self, t: TokenData) -> TokenData:
        data = self._send(
            "POST",
            "/v1/auth/token/refresh",
            body={"grant_type": "refresh_token", "refresh_token": t["refresh_token"]},
            bearer=t["access_token"],
        )
        return self._save(data)

    def _save(self, token: TokenData) -> TokenData:
        # Nomba has already rotated the session, so this token must not be lost even if the store fails.
        self._local = token
        for attempt in range(SET_RETRIES + 1):
            try:
                self._store.set(token)
                self._unsynced = False
                return token
            except Exception as e:  # noqa: BLE001 -- a caller's store may raise anything
                if attempt == SET_RETRIES:
                    self._unsynced = True
                    self._on_store_error(e)
                    return token
                time.sleep(0.1 * (attempt + 1))
        return token  # unreachable; keeps mypy happy

    def _read(self) -> TokenData | None:
        """The shared store's token, or this process's newer copy when the store is failing or behind."""
        try:
            stored = self._store.get()
        except Exception as e:  # noqa: BLE001 -- a caller's store may raise anything
            self._on_store_error(e)
            return self._local
        local = self._local
        # The store is authoritative unless our last write to it failed.
        if local is None or not self._unsynced:
            return stored
        return (
            local
            if stored is None or _expires_at(local) > _expires_at(stored)
            else stored
        )

    def _token_for_request(self, rejected: str | None = None) -> str:
        # Token failures happen before the request is sent, so they must never look like its outcome.
        try:
            return self._access_token(rejected)
        except Exception as e:
            raise TokenError(e) from e

    def _access_token(self, rejected: str | None) -> str:
        def usable(t: TokenData | None) -> bool:
            return (
                t is not None
                and t["access_token"] != rejected
                and _expires_at(t) - time.time() > REFRESH_MARGIN_S
            )

        cached = self._read()
        if cached is not None and usable(cached):
            return cached["access_token"]

        def renew() -> TokenData:
            # Another thread/instance may have renewed while we waited for the lock.
            current = self._read()
            if current is not None and usable(current):
                return current
            if current is None:
                return self._issue()
            try:
                return self._refresh(current)
            except NombaError as e:
                # Only a rejected refresh_token warrants a full re-issue; not network, 429 or 5xx errors.
                if e.status in (400, 401, 403):
                    return self._issue()
                raise

        return run_locked(self._store, renew, self._lock)["access_token"]

    # ---- requests --------------------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Any = None,
        query: Query | None = None,
        ok_codes: tuple[str, ...] = ("00",),
        idempotency_key: str | None = None,
        code_field: str = "code",
        description_field: str = "description",
        envelope: bool = False,
    ) -> Any:
        """Authenticated call. Issues or refreshes the token as needed.

        ``idempotency_key`` is tracked in ``OutcomeUnknownError`` for non-GET calls; it is
        never sent to Nomba. Put the endpoint's real idempotency field (e.g. ``merchantTxRef``)
        in ``body``. A random UUID is used if omitted.

        Returns the body's ``data`` (or ``(code, data)`` with ``envelope=True``).

        Raises:
            ValueError: ``path`` does not start with ``/``.
            TokenError: getting/refreshing the token failed; the request was never sent.
            NombaError: non-2xx, or a 2xx whose body code is not in ``ok_codes``.
            OutcomeUnknownError: a non-GET call failed without saying whether it was processed.
        """
        # The URL is base + path, so a path not starting with "/" could change the host and
        # send the bearer token there. Checked before the token is even read.
        if not path.startswith("/"):
            raise ValueError(f'path must start with "/", like "/v1/...", got {path!r}')
        params = {k: _qs_value(v) for k, v in (query or {}).items() if v is not None}
        url = f"{path}?{httpx.QueryParams(params)}" if params else path
        # One key for every attempt of this call, including the retry after a 401 token renewal.
        key = None if method == "GET" else (idempotency_key or str(uuid.uuid4()))
        token = self._token_for_request()
        opts: dict[str, Any] = {
            "body": body,
            "ok_codes": ok_codes,
            "idempotency_key": key,
            "code_field": code_field,
            "description_field": description_field,
            "envelope": envelope,
        }
        try:
            return self._send(method, url, bearer=token, **opts)
        except NombaError as e:
            # Docs: a 401 signals the access_token expired; renew it and retry once.
            if e.status != 401:
                raise
            return self._send(
                method, url, bearer=self._token_for_request(token), **opts
            )

    def report_outcome(self, event: dict[str, Any]) -> None:
        """Invokes the ``on_outcome`` hook, if any, swallowing any error it raises."""
        self._hook(self._on_outcome, event)

    @staticmethod
    def _hook(fn: Hook | None, info: dict[str, Any]) -> None:
        # A caller's hook must never break a request: its errors are logged instead.
        if fn is None:
            return
        try:
            fn(info)
        except Exception:
            log.warning("nomba: hook raised", exc_info=True)

    def _send(
        self,
        method: str,
        path: str,
        *,
        body: Any = None,
        bearer: str | None = None,
        ok_codes: tuple[str, ...] = ("00",),
        idempotency_key: str | None = None,
        code_field: str = "code",
        description_field: str = "description",
        envelope: bool = False,
    ) -> Any:
        """One logical request, retried only where that is verified safe:

        - 429: never processed, so always retried, GET or not.
        - GET: also retried on timeout, network error, 5xx or an in-flight 409.
        - A mutating call is NOT auto-retried on those: Nomba dedupes on a body field
          (``merchantTxRef`` etc.), so it fails after one attempt with ``OutcomeUnknownError``.
        - Any other 4xx, or a non-ok body code: a definite rejection, raised as is.
        """
        hook_path = path.split("?")[0]
        headers = {
            "accountId": self._account_id,
            "X-Nomba-Sdk-Version": SDK_VERSION,
            "User-Agent": f"nomba_python_sdk:v{SDK_VERSION}",
        }
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        attempt = 1
        while True:
            try:
                self._hook(
                    self._on_request,
                    {"method": method, "path": hook_path, "attempt": attempt},
                )
                started = time.monotonic()
                res = self._client.request(
                    method, self._base_url + path, json=body, headers=headers
                )
                try:
                    payload = res.json()
                except ValueError:
                    payload = None
                    if res.is_success:
                        raise _UnreadableResponse(
                            f"Unreadable response (HTTP {res.status_code})"
                        ) from None
                # Docs: a 200 does not always mean success; the body's code must be in ok_codes.
                code = payload.get(code_field) if isinstance(payload, dict) else None
                info: dict[str, Any] = {
                    "method": method,
                    "path": hook_path,
                    "attempt": attempt,
                    "http_status": res.status_code,
                    "duration_ms": int((time.monotonic() - started) * 1000),
                }
                if isinstance(code, str):
                    info["code"] = code
                self._hook(self._on_response, info)
                if (
                    not res.is_success
                    or not isinstance(payload, dict)
                    or not isinstance(code, str)
                    or code not in ok_codes
                ):
                    desc = (
                        payload.get(description_field)
                        if isinstance(payload, dict)
                        else None
                    )
                    raise build_error(
                        res.status_code,
                        code if isinstance(code, str) else str(res.status_code),
                        desc if isinstance(desc, str) else res.reason_phrase,
                        retry_after=_retry_after_seconds(res.headers.get("Retry-After"))
                        if res.status_code == 429
                        else None,
                    )
                data = payload.get("data")
                return (code, data) if envelope else data
            except (NombaError, _UnreadableResponse, httpx.TransportError) as e:
                status = e.status if isinstance(e, NombaError) else None
                # 409 is "same key still being processed" (retry) or a real key conflict
                # (definite): only the message tells them apart.
                in_flight = (
                    isinstance(e, NombaError)
                    and status == 409
                    and re.search(
                        r"being processed|retry", e.description, re.IGNORECASE
                    )
                    is not None
                )
                if (
                    status is not None
                    and status < 500
                    and status not in (408, 429)
                    and not in_flight
                ):
                    raise
                safe_to_repeat = status == 429 or method == "GET"
                if attempt < self._max_attempts and safe_to_repeat:
                    retry_after = e.retry_after if isinstance(e, NombaError) else None
                    if retry_after is not None:
                        delay = min(retry_after, 60.0)
                    else:
                        delay = self._retry_delay_s * 2 ** (attempt - 1)
                        delay += random.random() * delay * 0.2
                    time.sleep(delay)
                    attempt += 1
                    continue
                if status == 429 or not idempotency_key:
                    raise
                raise OutcomeUnknownError(
                    method, path, idempotency_key, attempt, e
                ) from e
