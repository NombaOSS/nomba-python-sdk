from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

# Ported from Node's src/types/v1/globals/collections.types.ts.


class InitiateInflowParams(TypedDict):
    # The customer's mobile money number.
    phoneNumber: str
    # Nomba POSTs here when the status changes. Must be publicly reachable.
    callbackUrl: str
    amount: float
    # ISO 4217, e.g. CDF.
    currency: str
    # A `code` from `inflowProviders`.
    topupVendor: str
    # Sent in the body; the API dedupes on it. Required to prevent double disbursement.
    idempotencyKey: str


@dataclass(frozen=True)
class InflowProvider:
    code: str | None = None
    displayName: str | None = None


@dataclass(frozen=True)
class InflowResult:
    transactionReference: str | None = None
    status: str | None = None
    message: str | None = None
    idempotencyKey: str | None = None


@dataclass(frozen=True)
class CollectionTransaction:
    transactionId: str | None = None
    coreUserId: str | None = None
    account: str | None = None
    status: str | None = None
    amount: float | None = None
    currency: str | None = None
    vendor: str | None = None
    gatewayMessage: str | None = None
    gatewayCode: str | None = None
