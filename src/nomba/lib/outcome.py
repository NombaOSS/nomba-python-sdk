"""Classifies a money-moving call as success, pending or failed, using only documented values.

Ported from the Node SDK's ``src/lib/outcome.ts`` and ``src/types/common/outcome.types.ts``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal, TypeVar

from nomba.http import HttpClient, Query
from nomba.lib.errors import (
    IdempotencyKeyAbsentError,
    NombaError,
    OutcomeUnknownError,
    UnconfirmedOutcomeError,
)

T = TypeVar("T")

# - success: done; safe to fulfil the order.
# - pending: not final, or not one the docs list. Wait for the webhook or requery.
# - failed: a definite rejection. Safe to tell the customer it failed.
Outcome = Literal["success", "pending", "failed"]

# Documented 4xx body codes (docs/api-basics/response-codes): definite rejections.
REJECTED: Mapping[str, Outcome] = {
    c: "failed" for c in ("400", "401", "403", "404", "422", "429")
}


@dataclass(frozen=True)
class OutcomeTable:
    """The body codes and ``data.status`` values one endpoint documents. Anything missing is pending."""

    codes: Mapping[str, Outcome]
    statuses: Mapping[str, Outcome] | None = None
    # Where the status lives in ``data``. Defaults to ``data["status"]`` when it is a str.
    status_of: Callable[[Any], str | None] | None = None


@dataclass(frozen=True)
class PendingInfo[T]:
    data: T | None = None
    code: str | None = None
    status: str | None = None
    idempotency_key: str | None = None
    # Why the call is pending when no readable response came back.
    cause: BaseException | None = None


@dataclass(frozen=True)
class FailedInfo:
    error: NombaError
    code: str


def classify(table: OutcomeTable, code: str, status: str | None) -> Outcome:
    """Anything the table does not list is pending: an undocumented value is never acted on."""
    by_code = table.codes.get(code, "pending")
    if by_code != "success" or table.statuses is None:
        return by_code
    return table.statuses.get(status, "pending") if status is not None else "pending"


def _default_status_of(data: Any) -> str | None:
    s = data.get("status") if isinstance(data, dict) else None
    return s if isinstance(s, str) else None


def settle(
    http: HttpClient,
    method: str,
    path: str,
    table: OutcomeTable,
    *,
    field: str,
    key: str | None,
    body: Any = None,
    query: Query | None = None,
    on_success: Callable[[Any], Any] | None = None,
    on_pending: Callable[[PendingInfo[Any]], Any] | None = None,
    on_failed: Callable[[FailedInfo], Any] | None = None,
) -> Any:
    """Makes one money-moving call and settles it into exactly one outcome.

    With a closure for that outcome, returns what the closure returns. Without one:
    success returns ``data``; pending raises ``UnconfirmedOutcomeError`` (or
    ``OutcomeUnknownError`` on a transport failure); failed raises ``NombaError``.

    ``field``/``key``: the body field holding the idempotency key (e.g. ``"merchantTxRef"``)
    and its value. Must be non-empty; the SDK never generates one.
    """
    if not isinstance(key, str) or not key.strip():
        raise IdempotencyKeyAbsentError(field, path)

    def report(
        outcome: Outcome, code: str | None, status: str | None, k: str | None = key
    ) -> None:
        event: dict[str, Any] = {"method": method, "path": path, "outcome": outcome}
        if code is not None:
            event["code"] = code
        if status is not None:
            event["status"] = status
        if k is not None:
            event["idempotency_key"] = k
        http.report_outcome(event)

    try:
        code, data = http.request(
            method,
            path,
            body=body,
            query=query,
            idempotency_key=key,
            # Only documented non-failure codes come back as data; the rest arrive as NombaError.
            ok_codes=tuple(c for c, o in table.codes.items() if o != "failed"),
            envelope=True,
        )
    except (NombaError, OutcomeUnknownError) as caught:
        e: NombaError | OutcomeUnknownError | UnconfirmedOutcomeError = caught
        # Only a documented rejection (by HTTP status or body code) is a failure. Anything else
        # (a 2xx with an unlisted code, a 409 key conflict, a 408) may mean it went through.
        if (
            isinstance(e, NombaError)
            and table.codes.get(str(e.status)) != "failed"
            and table.codes.get(e.code) != "failed"
        ):
            e = UnconfirmedOutcomeError(
                method, path, "code", e.code, None, None, key, e
            )
        if isinstance(e, NombaError):
            report("failed", e.code, None)
            if on_failed is None:
                raise
            return on_failed(FailedInfo(error=e, code=e.code))
        pkey = e.idempotency_key
        pcode = e.code if isinstance(e, UnconfirmedOutcomeError) else None
        report("pending", pcode, None, pkey)
        if on_pending is None:
            if e is caught:
                raise
            raise e from caught
        return on_pending(PendingInfo(code=pcode, idempotency_key=pkey, cause=e))

    status = (table.status_of or _default_status_of)(data)
    outcome = classify(table, code, status)
    report(outcome, code, status)
    if outcome == "success":
        return on_success(data) if on_success is not None else data
    if on_pending is not None:
        return on_pending(
            PendingInfo(data=data, code=code, status=status, idempotency_key=key)
        )
    # No on_pending: documented or not, pending always raises so it can never be mistaken for success.
    if table.codes.get(code) is None:
        reason: Literal["code", "status"] = "code"
    elif status is not None and (table.statuses or {}).get(status) is None:
        reason = "status"
    elif table.codes.get(code) == "pending":
        reason = "code"
    else:
        reason = "status"
    raise UnconfirmedOutcomeError(method, path, reason, code, status, data, key)
