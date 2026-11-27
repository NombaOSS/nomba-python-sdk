from __future__ import annotations

from dataclasses import dataclass
from typing import NotRequired, TypedDict

# Ported from Node's src/types/v1/requery/requery.types.ts.


class TransactionLookupParams(TypedDict):
    """Each field is independently optional per the docs, but the endpoint needs at least
    one to identify a transaction. Node expresses this as a 4-way discriminated union
    (one of the four required); a single all-optional TypedDict is the closest Python
    equivalent without a runtime check Node itself does not perform either."""

    transactionRef: NotRequired[str]
    merchantTxRef: NotRequired[str]
    # Online checkout order reference.
    orderReference: NotRequired[str]
    # Online checkout order id.
    orderId: NotRequired[str]


@dataclass(frozen=True)
class Transaction:
    id: str
    status: str
    amount: float
    source: str
    type: str
    gatewayMessage: str
    timeCreated: str
    fixedCharge: float | None = None
    customerBillerId: str | None = None
    posTid: str | None = None
    terminalId: str | None = None
    providerTerminalId: str | None = None
    rrn: str | None = None
    posSerialNumber: str | None = None
    posTerminalLabel: str | None = None
    stan: str | None = None
    paymentVendorReference: str | None = None
    userId: str | None = None
    posRrn: str | None = None
    merchantTxRef: str | None = None
