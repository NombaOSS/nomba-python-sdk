from __future__ import annotations

from typing import Unpack

from nomba.http import HttpClient
from nomba.lib.util import _build, _query
from nomba.v1.direct_debits.types import (
    CreatedMandate,
    CreateMandateParams,
    DebitMandateParams,
    ListMandatesParams,
    MandateDebitResult,
    MandatePage,
    MandateStatus,
    UpdatedMandateStatus,
    UpdateMandateStatusParams,
)

# Ported from Node's src/services/v1/direct-debits/direct-debits.service.ts (only a v1
# domain exists -- checked both v1 and v2 service paths). None of these methods call
# settle()/OutcomeTable in Node, so none are money-moving here either.


class DirectDebits:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create_mandate(self, **params: Unpack[CreateMandateParams]) -> CreatedMandate:
        """`POST /v1/direct-debits`. Creates a recurring debit mandate.
        `merchantReference` (in `params`) is the idempotency key.

        This endpoint's response envelope uses `responseCode`/`responseMessage` instead of
        the usual `code`/`description` -- confirmed from Node's call site.
        """
        return _build(
            CreatedMandate,
            self._http.request(
                "POST",
                "/v1/direct-debits",
                body=params,
                idempotency_key=params.get("merchantReference"),
                code_field="responseCode",
                description_field="responseMessage",
            ),
        )

    def get_mandate_status(self, mandate_id: str) -> MandateStatus:
        """`GET /v1/direct-debits/status?mandateId={mandateId}`. Looks up a mandate's status."""
        return _build(
            MandateStatus,
            self._http.request(
                "GET", "/v1/direct-debits/status" + _query({"mandateId": mandate_id})
            ),
        )

    def debit_mandate(self, **params: Unpack[DebitMandateParams]) -> MandateDebitResult:
        """`POST /v1/direct-debits/debit-mandate`. Debits an active mandate."""
        return _build(
            MandateDebitResult,
            self._http.request(
                "POST",
                "/v1/direct-debits/debit-mandate",
                body=params,
            ),
        )

    def list_mandates(self, **params: Unpack[ListMandatesParams]) -> MandatePage:
        """`GET /v1/direct-debits/mandates`. Lists mandates, paginated.

        `params["from"]` can't be passed as a keyword argument (`from` is a Python
        keyword) -- pass it via `**{"from": ..., **other_params}` instead.
        """
        return _build(
            MandatePage,
            self._http.request("GET", "/v1/direct-debits/mandates" + _query(params)),
        )

    def update_mandate_status(
        self, **params: Unpack[UpdateMandateStatusParams]
    ) -> UpdatedMandateStatus:
        """`PUT /v1/direct-debits/update-status`. Changes a mandate's status
        (`SUSPEND`/`ACTIVE`/`DELETE`)."""
        return _build(
            UpdatedMandateStatus,
            self._http.request("PUT", "/v1/direct-debits/update-status", body=params),
        )
