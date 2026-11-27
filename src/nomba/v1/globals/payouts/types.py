from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, NotRequired, TypedDict

# Ported from Node's src/types/v1/globals/payout.types.ts.

# "from" is a Python keyword, so the functional TypedDict syntax is required for this one.
ExchangeRatesParams = TypedDict(
    "ExchangeRatesParams",
    {
        # ISO 4217.
        "from": str,
        "to": str,
        "region": NotRequired[str],
    },
)


class ConvertMoneyParams(TypedDict):
    amount: float
    # ISO 4217 source currency.
    currency: str
    destinationCurrency: str
    # EXCHANGE for currency conversions.
    transactionType: str


class Beneficiary(TypedDict):
    beneficiaryEmail: NotRequired[str]
    securityQuestion: NotRequired[str]
    securityQuestionAnswer: NotRequired[str]
    # Canada only.
    transitNumber: NotRequired[str]
    beneficiaryAddress: NotRequired[str]
    beneficiaryCity: NotRequired[str]
    beneficiaryState: NotRequired[str]
    beneficiaryPostCode: NotRequired[str]


PaymentMethod = Literal[
    "BANK", "MobileMoney", "INTERAC", "FASTER_PAYMENTS", "SEPA", "ACH", "WIRE"
]


class AuthorizeExchangeParams(TypedDict):
    """``idempotencyKey`` is supplied separately, as ``authorize_exchange``'s
    ``idempotency_key`` positional argument -- not part of these kwargs."""

    amount: float
    sourceCurrency: str
    destinationCurrency: str
    senderName: str
    receiverName: str
    # ISO 3166-1 alpha-2.
    sourceCountryIsoCode: str
    destinationCountryIsoCode: str
    narration: NotRequired[str]
    # An `exchangeRateId` from `exchange_rates`.
    lockedExchangeRateId: NotRequired[str]


class AuthorizeTransferParams(TypedDict):
    """``idempotencyKey`` is supplied separately, as ``authorize_transfer``'s
    ``idempotency_key`` positional argument -- not part of these kwargs. Which fields
    are required depends on the payment method and corridor; see `payment_methods`."""

    amount: float
    sourceCurrency: str
    destinationCurrency: str
    receiverName: str
    sourceCountryIsoCode: str
    destinationCountryIsoCode: str
    paymentMethod: PaymentMethod
    accountType: Literal["INDIVIDUAL", "CORPORATE"]
    # Account number, IBAN, or phone number for MobileMoney.
    accountNumber: NotRequired[str]
    # Bank code, sort code, SWIFT/BIC or institution number, depending on the method.
    institutionCode: NotRequired[str]
    institutionName: NotRequired[str]
    # Required for ACH and WIRE.
    bankAccountType: NotRequired[Literal["CHECKING", "SAVINGS"]]
    # Required for ACH, WIRE and SEPA: a code from `payment_methods`'s purposeOfPayments.
    purposeOfPayment: NotRequired[str]
    narration: NotRequired[str]
    lockedExchangeRateId: NotRequired[str]
    bankAddress: NotRequired[str]
    bankCity: NotRequired[str]
    bankState: NotRequired[str]
    bankZipCode: NotRequired[str]
    beneficiary: NotRequired[Beneficiary]


class InstitutionProvidersParams(TypedDict):
    # true for mobile money providers, false for banks and other institutions.
    isMobileMoney: NotRequired[bool]
    # ISO 3166-1 alpha-2 destination country.
    countryIsoCode: NotRequired[str]


class PaymentMethodsParams(TypedDict):
    destinationCountryIsoCode: NotRequired[str]
    destinationCurrency: NotRequired[str]
    code: NotRequired[str]
    name: NotRequired[str]


@dataclass(frozen=True)
class PayoutAccount:
    accountId: str | None = None
    name: str | None = None
    currency: str | None = None
    balance: float | None = None
    availableBalance: float | None = None
    status: str | None = None
    operationRegion: str | None = None


@dataclass(frozen=True)
class ExchangeRate:
    exchangeRateId: str | None = None
    currencyPairName: str | None = None
    bidRate: str | None = None
    askRate: str | None = None
    midRate: str | None = None
    createdAt: str | None = None
    tradeRegion: str | None = None
    tradeContext: str | None = None
    updatedAt: str | None = None


@dataclass(frozen=True)
class Conversion:
    fromAmount: float | None = None
    fromCurrency: str | None = None
    fromFormatted: str | None = None
    toAmount: float | None = None
    toCurrency: str | None = None
    toFormatted: str | None = None
    spreadAmount: float | None = None
    spreadCurrency: str | None = None
    exchangeRateId: str | None = None
    currencyPairName: str | None = None
    feeAmount: float | None = None
    feeCurrency: str | None = None
    feeExpression: str | None = None


@dataclass(frozen=True)
class InstitutionProvider:
    code: str | None = None
    displayName: str | None = None


@dataclass(frozen=True)
class PaymentMethodInfo:
    code: str | None = None
    displayName: str | None = None
    purposeOfPaymentRequired: bool | None = None
    purposeOfPayments: list[dict[str, Any]] | None = None
    requiredFields: list[str] | None = None
    optionalFields: list[str] | None = None
    accountTypes: list[str] | None = None
    bankAccountTypes: list[str] | None = None
    supportedCorridors: list[dict[str, Any]] | None = None


@dataclass(frozen=True)
class PayoutTransaction:
    transactionId: str | None = None
    status: str | None = None
    coreStatus: str | None = None
    type: str | None = None
    createdAt: str | None = None
    idempotencyKey: str | None = None
