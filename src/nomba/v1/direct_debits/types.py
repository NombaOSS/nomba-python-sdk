from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, NotRequired, TypedDict

# Ported from Node's src/types/v1/direct-debits/direct-debits.types.ts.

Frequency = Literal[
    "VARIABLE",
    "WEEKLY",
    "EVERY_TWO_WEEKS",
    "MONTHLY",
    "EVERY_TWO_MONTHS",
    "EVERY_THREE_MONTHS",
    "EVERY_FOUR_MONTHS",
    "EVERY_FIVE_MONTHS",
    "EVERY_SIX_MONTHS",
    "EVERY_SEVEN_MONTHS",
    "EVERY_EIGHT_MONTHS",
    "EVERY_NINE_MONTHS",
    "EVERY_TEN_MONTHS",
    "EVERY_ELEVEN_MONTHS",
    "EVERY_TWELVE_MONTHS",
]


class CreateMandateParams(TypedDict):
    customerAccountNumber: str
    bankCode: str
    customerName: str
    customerAddress: NotRequired[str]
    customerAccountName: str
    amount: float
    frequency: Frequency
    narration: NotRequired[str]
    customerPhoneNumber: NotRequired[str]
    # Numeric string (0-9). An idempotency-style tracking id; must be unique per transaction.
    merchantReference: str
    startDate: str
    endDate: str
    customerEmail: str
    startImmediately: NotRequired[bool]


class DebitMandateParams(TypedDict):
    mandateId: str
    # Decimal string, e.g. "110.00"
    amount: str


# "from" is a Python keyword, so the functional TypedDict syntax is required for this field.
ListMandatesParams = TypedDict(
    "ListMandatesParams",
    {
        "page": int,
        "pageSize": int,
        # date, e.g. "2025-08-01"
        "from": NotRequired[str],
        "to": NotRequired[str],
        "status": NotRequired[str],
    },
)


class UpdateMandateStatusParams(TypedDict):
    mandateId: str
    status: Literal["SUSPEND", "ACTIVE", "DELETE"]


@dataclass(frozen=True)
class CreatedMandate:
    mandateId: str | None = None
    merchantReference: str | None = None
    phoneNumber: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class MandateStatus:
    customerAccountName: str | None = None
    mandateId: str | None = None
    customerAccountNumber: str | None = None
    mandateStatus: str | None = None
    rejectionComment: str | None = None
    mandateAdviceStatus: str | None = None


@dataclass(frozen=True)
class MandateDebitResult:
    mandateId: str | None = None
    status: str | None = None
    amount: str | None = None
    message: str | None = None


@dataclass(frozen=True)
class MandatePage:
    items: list[dict[str, Any]] | None = None
    page: int | None = None
    pageSize: int | None = None
    totalItems: int | None = None
    totalPages: int | None = None
    hasMore: bool | None = None


@dataclass(frozen=True)
class UpdatedMandateStatus:
    mandateId: str | None = None
    mandateStatus: str | None = None
