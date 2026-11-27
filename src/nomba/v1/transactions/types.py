from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, NotRequired, TypedDict

from nomba.v2.transfers.types import TransferType

# Ported from Node's src/types/v1/transactions/transactions.types.ts and
# src/types/v1/requery/requery.types.ts (Transaction).


class FilterTransactionsParams(TypedDict):
    transactionRef: NotRequired[str]
    # Broader than Transaction's own status: includes filter-only states like NEW and
    # PENDING_PAYMENT.
    status: NotRequired[
        Literal[
            "NEW",
            "PENDING_PAYMENT",
            "PAYMENT_SUCCESSFUL",
            "PAYMENT_FAILED",
            "PENDING_BILLING",
            "SUCCESS",
            "REFUND",
        ]
    ]
    source: NotRequired[Literal["api", "pos", "web", "android_app", "ios_app"]]
    type: NotRequired[TransferType]
    terminalId: NotRequired[str]
    # Retrieval Reference Number.
    rrn: NotRequired[str]
    merchantTxRef: NotRequired[str]
    # Online checkout order reference.
    orderReference: NotRequired[str]
    # Online checkout order id.
    orderId: NotRequired[str]


@dataclass(frozen=True)
class BankTransaction:
    amount: float
    currency: str
    meta: dict[str, Any]
    status: str
    timeUpdated: str
    walletBalance: float
    transactionType: str


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


@dataclass(frozen=True)
class VirtualAccountTransaction:
    id: str
    status: str
    amount: str
    timeCreated: str
    fixedCharge: str | None = None
    source: str | None = None
    type: str | None = None
    timeUpdated: str | None = None
    walletCurrency: str | None = None
    walletBalance: str | None = None
    paymentVendorReference: str | None = None
    senderName: str | None = None
    recipientAccountNumber: str | None = None
    recipientAccountName: str | None = None
    recipientAccountType: str | None = None
    sessionId: str | None = None
    accountNumber: str | None = None
    bankCode: str | None = None
    bankName: str | None = None
    entryType: str | None = None
    narration: str | None = None
    currency: str | None = None
