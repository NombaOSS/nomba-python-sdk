from __future__ import annotations

import json as _json
from typing import Any, Unpack

from nomba.http import HttpClient
from nomba.lib.util import _build, _path_id, _query
from nomba.v1.charge.types import (
    ChargeOrder,
    ChargeTransactionDetails,
    FlashAccount,
    SubmitCardDetailsParams,
    SubmitCardDetailsResult,
    SubmitCardOtpResult,
)
from nomba.v1.checkout import CheckoutResult, TokenizedCardData

# Ported from Node's src/services/v1/charge/charge.service.ts (method list; only v1 exists --
# there is no src/services/v2/charge in Node).
# None of charge's methods call settle()/OutcomeTable in Node -- every one of them, including
# the ones documenting an idempotency key and an OutcomeUnknownError possibility, stays a plain
# http.request call there, the same as checkout's non-refund methods. So none of these route
# through settle() either. `idempotency_key` mirrors Node's per-call `idempotencyKey`: it is
# only reported in OutcomeUnknownError, never sent, and never enables retries.


class Charge:
    """Build your own checkout on top of an order created with `nomba.v1.checkout.create_order`.
    Flow: get_order, submit_card_details, submit_card_otp, then fetch_transaction_details."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def get_order(self, order_reference: str) -> ChargeOrder:
        """`GET /v1/checkout/order/{orderReference}`. The order's details."""
        return _build(
            ChargeOrder,
            self._http.request(
                "GET", f"/v1/checkout/order/{_path_id(order_reference)}"
            ),
        )

    def submit_card_details(
        self, **params: Unpack[SubmitCardDetailsParams]
    ) -> SubmitCardDetailsResult:
        """`POST /v1/checkout/checkout-card-detail`. Submits card details to charge; check
        `responseCode` on the result. `params["cardDetails"]`, if a dict, is JSON-stringified
        first (pass an already-encoded string when data encryption is in use).
        `params["orderReference"]`, if given, is used as the idempotency key."""
        body: dict[str, Any] = dict(params)
        card_details = body.get("cardDetails")
        if isinstance(card_details, dict):
            body["cardDetails"] = _json.dumps(card_details)
        return _build(
            SubmitCardDetailsResult,
            self._http.request(
                "POST",
                "/v1/checkout/checkout-card-detail",
                body=body,
                idempotency_key=params.get("orderReference"),
            ),
        )

    def submit_card_otp(
        self, otp: str, order_reference: str, transaction_id: str
    ) -> SubmitCardOtpResult:
        """`POST /v1/checkout/checkout-card-otp`. `transaction_id` is the idempotency key, the
        one returned by `submit_card_details`."""
        return _build(
            SubmitCardOtpResult,
            self._http.request(
                "POST",
                "/v1/checkout/checkout-card-otp",
                body={
                    "otp": otp,
                    "orderReference": order_reference,
                    "transactionId": transaction_id,
                },
                idempotency_key=transaction_id,
            ),
        )

    def resend_otp(self, order_reference: str) -> CheckoutResult:
        """`POST /v1/checkout/resend-otp`. Resends the payment OTP to the customer's phone.
        `order_reference` is the idempotency key."""
        return _build(
            CheckoutResult,
            self._http.request(
                "POST",
                "/v1/checkout/resend-otp",
                body={"orderReference": order_reference},
                idempotency_key=order_reference,
            ),
        )

    def fetch_transaction_details(
        self, order_reference: str
    ) -> ChargeTransactionDetails:
        """`POST /v1/checkout/confirm-transaction-receipt`. The status after the OTP is
        submitted or a transfer is made. Node does not key this call for idempotency, so it is
        not auto-retried."""
        return _build(
            ChargeTransactionDetails,
            self._http.request(
                "POST",
                "/v1/checkout/confirm-transaction-receipt",
                body={"orderReference": order_reference},
            ),
        )

    def fetch_flash_account(self, order_reference: str) -> FlashAccount:
        """`GET /v1/checkout/get-checkout-kta/{orderReference}`. A Flash account number the
        customer can pay by transfer."""
        return _build(
            FlashAccount,
            self._http.request(
                "GET", f"/v1/checkout/get-checkout-kta/{_path_id(order_reference)}"
            ),
        )

    def cancel_transaction(
        self, transaction_id: str, force_cancel: bool
    ) -> CheckoutResult:
        """`POST /v1/checkout/transaction/cancel`. Cancels an incomplete checkout transaction.
        `transaction_id` is the idempotency key."""
        return _build(
            CheckoutResult,
            self._http.request(
                "POST",
                "/v1/checkout/transaction/cancel",
                body={"transactionId": transaction_id, "forceCancel": force_cancel},
                idempotency_key=transaction_id,
            ),
        )

    def request_saved_cards_otp(self, order_reference: str) -> CheckoutResult:
        """`POST /v1/checkout/user-card/saved-card/auth`. Sends an OTP; use when `get_order`
        says the user has saved cards. `order_reference` is the idempotency key."""
        return _build(
            CheckoutResult,
            self._http.request(
                "POST",
                "/v1/checkout/user-card/saved-card/auth",
                body={"orderReference": order_reference},
                idempotency_key=order_reference,
            ),
        )

    def get_saved_cards(
        self, order_reference: str, otp: str
    ) -> list[TokenizedCardData]:
        """`GET /v1/checkout/user-card/{orderReference}`. Needs the OTP from
        `request_saved_cards_otp`."""
        data = self._http.request(
            "GET",
            f"/v1/checkout/user-card/{_path_id(order_reference)}{_query({'otp': otp})}",
        )
        return [
            _build(TokenizedCardData, c) for c in (data.get("tokenizedCardData") or [])
        ]

    def request_save_card_otp(
        self, order_reference: str, phone_number: str
    ) -> CheckoutResult:
        """`POST /v1/checkout/user-card/auth`. Sends an OTP before saving a card; call after a
        successful payment. `order_reference` is the idempotency key."""
        return _build(
            CheckoutResult,
            self._http.request(
                "POST",
                "/v1/checkout/user-card/auth",
                body={"orderReference": order_reference, "phoneNumber": phone_number},
                idempotency_key=order_reference,
            ),
        )

    def submit_save_card_otp(
        self, order_reference: str, phone_number: str, otp: str
    ) -> CheckoutResult:
        """`POST /v1/checkout/user-card`. Submits the OTP from `request_save_card_otp`, which
        saves the card for later use. `order_reference` is the idempotency key."""
        return _build(
            CheckoutResult,
            self._http.request(
                "POST",
                "/v1/checkout/user-card",
                body={
                    "orderReference": order_reference,
                    "phoneNumber": phone_number,
                    "otp": otp,
                },
                idempotency_key=order_reference,
            ),
        )
