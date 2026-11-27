from nomba.lib.errors import (
    AuthenticationError,
    IdempotencyKeyAbsentError,
    NombaError,
    NotFoundError,
    OutcomeUnknownError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    TokenError,
    UnconfirmedOutcomeError,
    ValidationError,
    build_error,
    is_pending,
)


def _unknown() -> OutcomeUnknownError:
    return OutcomeUnknownError("POST", "/v2/transfers/bank", "ref-1", 1, TimeoutError())


def _unconfirmed() -> UnconfirmedOutcomeError:
    return UnconfirmedOutcomeError("POST", "/p", "code", "X9", None, None, "ref-1")


def test_is_pending():
    assert is_pending(_unknown()) is True
    assert is_pending(_unconfirmed()) is True
    assert is_pending(NombaError(400, "400", "bad")) is False
    assert is_pending(TokenError(ValueError("bad creds"))) is False


def test_errors_carry_node_fields():
    e = _unknown()
    assert (e.method, e.path, e.idempotency_key, e.attempts) == (
        "POST",
        "/v2/transfers/bank",
        "ref-1",
        1,
    )
    u = _unconfirmed()
    assert (u.reason, u.code, u.idempotency_key) == ("code", "X9", "ref-1")
    k = IdempotencyKeyAbsentError("merchantTxRef", "/v2/transfers/bank")
    assert (k.field, k.path) == ("merchantTxRef", "/v2/transfers/bank")
    assert str(NombaError(400, "400", "bad")) == "[400] bad"


def test_build_error_picks_most_specific_subclass():
    cases = {
        400: ValidationError,
        422: ValidationError,
        401: AuthenticationError,
        403: PermissionDeniedError,
        404: NotFoundError,
        429: RateLimitError,
        500: ServerError,
        503: ServerError,
        418: NombaError,  # no specific subclass; falls back to the base
    }
    for status, expected in cases.items():
        err = build_error(status, str(status), "x")
        assert type(err) is expected
        assert isinstance(err, NombaError)  # except NombaError still catches it


def test_build_error_carries_retry_after():
    err = build_error(429, "429", "slow down", retry_after=12.5)
    assert isinstance(err, RateLimitError)
    assert err.retry_after == 12.5


def test_pending_and_token_errors_are_not_nomba_errors():
    # As in Node: `except NombaError` (a definite rejection) must never catch a call
    # whose outcome is unknown, or one that was never sent.
    for cls in (
        OutcomeUnknownError,
        UnconfirmedOutcomeError,
        TokenError,
        IdempotencyKeyAbsentError,
    ):
        assert not issubclass(cls, NombaError)
