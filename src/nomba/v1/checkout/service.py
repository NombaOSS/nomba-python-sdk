from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any, Unpack

from nomba.http import HttpClient
from nomba.lib.outcome import REJECTED, OutcomeTable, settle
from nomba.lib.paginate import paginate
from nomba.lib.util import _build, _query
from nomba.v1.checkout.types import (
    ChargeTokenizedCardResult,
    CheckoutOrder,
    CheckoutOrderCreated,
    CheckoutResult,
    CheckoutTransaction,
    CreateCheckoutOrderParams,
    FetchCheckoutTransactionParams,
    ListTokenizedCardsParams,
    RefundCheckoutTransactionParams,
    TokenizedCardData,
    TokenizedCardResult,
    UpdatedTokenizedCard,
)

__all__ = ["REFUND_OUTCOMES", "Checkout"]

# Ported from Node's src/services/v1/checkout/checkout.service.ts (method list).
# Only `refund` uses settle()/OutcomeTable in Node -- the rest (createOrder, cancelOrder,
# chargeTokenizedCard, updateTokenizedCard, deleteTokenizedCard) stay plain there too, despite
# some of them documenting an idempotency key and an OutcomeUnknownError possibility.


# The refund endpoint documents code "00" and a `success` boolean in data, not a `status`
# string -- `_refund_status_of` adapts it for `settle()`. The docs don't say `false` is final,
# so it is pending (requery before refunding again), like Node's comment on this table.
def _refund_status_of(data: Any) -> str | None:
    ok = data.get("success") if isinstance(data, dict) else None
    return ("true" if ok else "false") if isinstance(ok, bool) else None


REFUND_OUTCOMES = OutcomeTable(
    codes={"00": "success", **REJECTED},
    statuses={"true": "success", "false": "pending"},
    status_of=_refund_status_of,
)


def _tokenized_cards_page(
    data: dict[str, Any],
) -> tuple[list[TokenizedCardData], str | None]:
    results = [
        _build(TokenizedCardData, c) for c in data.get("tokenizedCardDataList") or []
    ]
    next_page = data.get("nextPage")
    cursor = next_page if next_page and next_page != "0" else None
    return results, cursor


class Checkout:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create_order(
        self, order: CheckoutOrder, **params: Unpack[CreateCheckoutOrderParams]
    ) -> CheckoutOrderCreated:
        """`POST /v1/checkout/order`. Send the customer to `checkoutLink` to pay.
        `order["orderReference"]`, if given, is used as the idempotency key."""
        ref = order.get("orderReference")
        return _build(
            CheckoutOrderCreated,
            self._http.request(
                "POST",
                "/v1/checkout/order",
                body={"order": order, **params},
                idempotency_key=ref,
            ),
        )

    def fetch_transaction(
        self, **params: Unpack[FetchCheckoutTransactionParams]
    ) -> CheckoutTransaction:
        """`GET /v1/checkout/transaction`. Looks up a transaction, e.g. by `idType`/`id`."""
        return _build(
            CheckoutTransaction,
            self._http.request("GET", f"/v1/checkout/transaction{_query(params)}"),
        )

    def cancel_order(self, order_reference: str) -> CheckoutResult:
        """`POST /v1/checkout/order/cancel`. Only for orders not yet paid; use `refund` after
        payment. `order_reference` is used as the idempotency key."""
        return _build(
            CheckoutResult,
            self._http.request(
                "POST",
                "/v1/checkout/order/cancel",
                body={"orderReference": order_reference},
                idempotency_key=order_reference,
            ),
        )

    def refund(
        self,
        transaction_id: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
        **params: Unpack[RefundCheckoutTransactionParams],
    ) -> Any:
        """`POST /v1/checkout/refund`. `transaction_id` is the idempotency key.

        Without closures: success returns the refund data; pending/undocumented raises
        `UnconfirmedOutcomeError`; failed raises `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            "/v1/checkout/refund",
            REFUND_OUTCOMES,
            field="transactionId",
            key=transaction_id,
            body={**params, "transactionId": transaction_id},
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )

    def charge_tokenized_card(
        self, token_key: str, order: CheckoutOrder | None = None
    ) -> ChargeTokenizedCardResult:
        """`POST /v1/checkout/tokenized-card-payment`. Check `status` on the result: if
        `otpRequired` is true, call `submit_card_otp`-equivalent with `transactionId` and
        `orderReference`. `order["orderReference"]`, if given, is used as the idempotency key."""
        ref = order.get("orderReference") if order is not None else None
        body: dict[str, Any] = {"tokenKey": token_key}
        if order is not None:
            body["order"] = order
        return _build(
            ChargeTokenizedCardResult,
            self._http.request(
                "POST",
                "/v1/checkout/tokenized-card-payment",
                body=body,
                idempotency_key=ref,
            ),
        )

    def list_tokenized_cards(
        self, **params: Unpack[ListTokenizedCardsParams]
    ) -> tuple[list[TokenizedCardData], str | None]:
        """`GET /v1/checkout/tokenized-card-data`. Lists saved, tokenized cards."""
        data = self._http.request(
            "GET", f"/v1/checkout/tokenized-card-data{_query(params)}"
        )
        return _tokenized_cards_page(data)

    def iterate_tokenized_cards(
        self, **params: Unpack[ListTokenizedCardsParams]
    ) -> Iterator[TokenizedCardData]:
        """Every tokenized card matching the filters, across all pages. Starts at
        `params["page"]` if given."""

        def fetch(cursor: str | None) -> tuple[list[TokenizedCardData], str | None]:
            page_params: dict[str, Any] = dict(params)
            if cursor:
                page_params["page"] = cursor
            return self.list_tokenized_cards(**page_params)

        return paginate(fetch)

    def update_tokenized_card(
        self, token_key: str, current_email_address: str, new_email_address: str
    ) -> UpdatedTokenizedCard:
        """`POST /v1/checkout/tokenized-card-data`. `token_key` is the idempotency key."""
        return _build(
            UpdatedTokenizedCard,
            self._http.request(
                "POST",
                "/v1/checkout/tokenized-card-data",
                body={
                    "tokenKey": token_key,
                    "currentEmailAddress": current_email_address,
                    "newEmailAddress": new_email_address,
                },
                idempotency_key=token_key,
            ),
        )

    def delete_tokenized_card(self, token_key: str) -> TokenizedCardResult:
        """`DELETE /v1/checkout/tokenized-card-data`. `token_key` is the idempotency key."""
        return _build(
            TokenizedCardResult,
            self._http.request(
                "DELETE",
                "/v1/checkout/tokenized-card-data",
                body={"tokenKey": token_key},
                idempotency_key=token_key,
            ),
        )
