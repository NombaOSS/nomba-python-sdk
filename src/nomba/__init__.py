"""Python SDK for the Nomba payments API.

Construct a :class:`nomba.Nomba` client and call through its domain
attributes, e.g. ``Nomba(...).transfers.bank_transfer(...)``. See the
project README for setup and usage examples.
"""

from nomba.client import Nomba
from nomba.http import HttpClient
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
    is_pending,
)
from nomba.lib.token_store import MemoryTokenStore, TokenData, TokenStore
from nomba.lib.webhooks import verify_signature

__all__ = [
    "AuthenticationError",
    "HttpClient",
    "IdempotencyKeyAbsentError",
    "MemoryTokenStore",
    "Nomba",
    "NombaError",
    "NotFoundError",
    "OutcomeUnknownError",
    "PermissionDeniedError",
    "RateLimitError",
    "ServerError",
    "TokenData",
    "TokenError",
    "TokenStore",
    "UnconfirmedOutcomeError",
    "ValidationError",
    "is_pending",
    "verify_signature",
]

# Placeholder; release tooling overwrites this.
__version__ = "0.0.0"
