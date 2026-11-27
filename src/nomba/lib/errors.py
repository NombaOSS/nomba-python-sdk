"""The SDK's error hierarchy, ported from the Node SDK's ``src/lib/errors.ts``.

Only ``NombaError`` means "the API definitely rejected this". ``OutcomeUnknownError``,
``UnconfirmedOutcomeError``, ``TokenError`` and ``IdempotencyKeyAbsentError`` are
deliberately NOT subclasses of it (as in Node), so ``except NombaError`` can never treat a
payment that may have gone through as failed.
"""

from __future__ import annotations

from typing import Any, Literal


class NombaError(Exception):
    """Any non-2xx response, or a 2xx whose body code is not one the call accepts.

    Raised as the most specific subclass below that matches the HTTP status, so
    ``except NotFoundError`` (etc.) works; ``except NombaError`` still catches all of them.
    """

    def __init__(
        self,
        status: int,
        code: str,
        description: str,
        *,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(f"[{code}] {description}")
        self.status = status
        self.code = code
        self.description = description
        # Seconds from the 429 response's Retry-After header, when present.
        self.retry_after = retry_after


class AuthenticationError(NombaError):
    """401: the access token was rejected even after a refresh-and-retry."""


class PermissionDeniedError(NombaError):
    """403."""


class NotFoundError(NombaError):
    """404."""


class ValidationError(NombaError):
    """400 or 422."""


class RateLimitError(NombaError):
    """429. ``retry_after`` is the seconds from the response's ``Retry-After`` header,
    when Nomba sent one."""


class ServerError(NombaError):
    """5xx."""


_BY_STATUS: dict[int, type[NombaError]] = {
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    400: ValidationError,
    422: ValidationError,
    429: RateLimitError,
}


def build_error(
    status: int, code: str, description: str, *, retry_after: float | None = None
) -> NombaError:
    """A ``NombaError``, as the most specific subclass ``status`` matches."""
    cls = _BY_STATUS.get(status, ServerError if status >= 500 else NombaError)
    return cls(status, code, description, retry_after=retry_after)


class OutcomeUnknownError(Exception):
    """A mutating request failed in a way that does not say whether it was processed
    (timeout, network error, 5xx, or a 409). The SDK makes one attempt and does not retry:
    check its status (webhook or requery) before retrying it yourself with the same
    ``idempotency_key``."""

    def __init__(
        self,
        method: str,
        path: str,
        idempotency_key: str,
        attempts: int,
        cause: BaseException,
    ) -> None:
        super().__init__(
            f'Outcome unknown for {method} {path} (idempotencyKey "{idempotency_key}"); '
            "it may have been processed. Check its status (webhook or requery) before "
            "retrying it yourself. Do not send it as a new request with a different reference."
        )
        self.method = method
        self.path = path
        self.idempotency_key = idempotency_key
        self.attempts = attempts
        self.__cause__ = cause


class UnconfirmedOutcomeError(Exception):
    """A money-moving call got a readable answer whose body code or ``data.status`` is not
    one the docs list for that endpoint. It may still complete: wait for the webhook or
    requery before refunding or retrying."""

    def __init__(
        self,
        method: str,
        path: str,
        reason: Literal["code", "status"],
        code: str | None,
        status: str | None,
        data: Any,
        idempotency_key: str | None,
        cause: BaseException | None = None,
    ) -> None:
        if reason == "code":
            what = f'code "{code}"'
        elif status is None:
            what = "missing data.status"
        else:
            what = f'status "{status}"'
        super().__init__(
            f"Unconfirmed outcome for {method} {path}: undocumented {what}. "
            "It may still complete; wait for the webhook or requery before acting."
        )
        self.method = method
        self.path = path
        self.reason = reason
        self.code = code
        self.status = status
        self.data = data
        self.idempotency_key = idempotency_key
        self.__cause__ = cause


class TokenError(Exception):
    """Getting or renewing the access token failed, so the request was never sent."""

    def __init__(self, cause: BaseException) -> None:
        super().__init__(
            f"Could not get an access token, so the request was not sent: {cause}"
        )
        self.__cause__ = cause


class IdempotencyKeyAbsentError(Exception):
    """A money-moving request was attempted without a caller-supplied idempotency key.
    The SDK never generates one for money-moving calls (risk of double disbursement)."""

    def __init__(self, field: str, path: str) -> None:
        super().__init__(
            f'Idempotency key required: set "{field}" in the request body for {path}. '
            "The SDK does not generate random keys for money-moving operations to prevent "
            "double disbursement."
        )
        self.field = field
        self.path = path


def is_pending(err: BaseException) -> bool:
    """True when a call's result is not final: wait for the webhook or requery, never
    refund or resend."""
    return isinstance(err, (OutcomeUnknownError, UnconfirmedOutcomeError))
