from __future__ import annotations

import httpx

from nomba.client import Nomba
from nomba.v1.accounts import AccountBalance
from nomba.v1.betting import BettingProvider
from nomba.v1.cable import CablePlan
from nomba.v1.charge import ChargeOrder
from nomba.v1.checkout import CheckoutTransaction
from nomba.v1.data import DataPlan
from nomba.v1.direct_debits import MandateStatus
from nomba.v1.electricity import ElectricityProvider
from nomba.v1.globals.collections import InflowProvider
from nomba.v1.globals.payouts import PayoutAccount
from nomba.v1.requery import Transaction as RequeryTransaction
from nomba.v1.terminals import Terminal
from nomba.v1.transactions import BankTransaction
from nomba.v1.virtual_accounts import VirtualAccount
from nomba.v2.electricity import MeterLookupResult
from nomba.v2.transfers import Bank

# Maps each request path to its canned success envelope. One MockTransport serves every
# domain call below -- the point of this test is "is every domain wired and callable",
# not per-method correctness (each domain's own test file already covers that).
RESPONSES: dict[str, object] = {
    "/v1/accounts/balance": {"amount": "100.0", "currency": "NGN", "timeCreated": "t"},
    "/v1/transactions/bank": {"results": [], "cursor": None},
    "/v1/accounts/virtual/va1": {
        "createdAt": "t",
        "accountHolderId": "h",
        "accountRef": "r",
        "bvn": "b",
        "accountName": "n",
        "bankName": "bn",
        "bankAccountName": "ban",
        "bankAccountNumber": "123",
        "currency": "NGN",
    },
    "/v1/terminals/assign": {
        "terminalId": "tid",
        "serialNumber": "sn",
        "accountId": "aid",
        "parentAccountId": "pid",
        "merchantName": "m",
        "terminalLabel": "l",
        "createdAt": "t",
        "updatedAt": "t",
    },
    "/v1/transactions/requery/s1": {
        "id": "id1",
        "status": "SUCCESS",
        "amount": 1.0,
        "source": "s",
        "type": "t",
        "gatewayMessage": "ok",
        "timeCreated": "t",
    },
    "/v1/checkout/transaction": {},
    "/v1/transfers/banks": [
        {"code": "044", "name": "Access Bank", "nipCode": "044", "logo": ""}
    ],
    "/v1/checkout/order/o1": {},
    "/v1/direct-debits/status": {},
    "/v1/global-collection/drc/inflow/providers": [],
    "/v1/global-payout/accounts": [],
    "/v1/bill/electricity/discos": [],
    "/v1/bill/cableTvProduct": [],
    "/v1/bill/betting/providers": [],
    "/v1/bill/data-plan/mtn": [],
    "/v2/bill/topup": {"status": "SUCCESS"},
    "/v2/bill/data": {"status": "SUCCESS"},
    "/v2/bill/electricity/lookup": {},
    "/v2/bill/cabletv": {"status": "SUCCESS"},
    "/v2/bill/betting": {"status": "SUCCESS"},
}


def _handler(req: httpx.Request) -> httpx.Response:
    path = req.url.path
    if path not in RESPONSES:
        raise AssertionError(f"smoke test has no canned response for {path}")
    return httpx.Response(200, json={"code": "00", "data": RESPONSES[path]})


def test_every_domain_is_wired_and_callable(fake_http):
    http = fake_http(_handler)
    client = Nomba(client_id="x", client_secret="y", account_id="z", http_client=http)

    assert isinstance(client.accounts.get_parent_balance(), AccountBalance)

    txns, _cursor = client.transactions.list_bank_transactions()
    assert isinstance(txns, list)
    for t in txns:
        assert isinstance(t, BankTransaction)

    assert isinstance(client.virtual_accounts.get("va1"), VirtualAccount)
    assert isinstance(client.terminals.assign_to_parent(serialNumber="sn1"), Terminal)
    assert isinstance(client.requery.requery_by_session("s1"), RequeryTransaction)
    assert isinstance(client.checkout.fetch_transaction(), CheckoutTransaction)
    assert all(isinstance(b, Bank) for b in client.transfers.list_banks())
    assert isinstance(client.charge.get_order("o1"), ChargeOrder)
    assert isinstance(client.direct_debits.get_mandate_status("m1"), MandateStatus)
    assert all(
        isinstance(p, InflowProvider) for p in client.collections.inflow_providers()
    )
    assert all(isinstance(a, PayoutAccount) for a in client.payouts.list_accounts())
    assert all(
        isinstance(p, ElectricityProvider)
        for p in client.bill_electricity.get_electricity_providers()
    )
    assert all(
        isinstance(p, CablePlan)
        for p in client.bill_cable.get_cable_plans(cableTvType="dstv")
    )
    assert all(
        isinstance(p, BettingProvider)
        for p in client.bill_betting.get_betting_providers()
    )
    assert all(isinstance(p, DataPlan) for p in client.bill_data.get_data_plans("mtn"))

    assert (
        client.airtime.buy_airtime(
            "ref1", amount=100, phoneNumber="08011112222", network="MTN"
        )["status"]
        == "SUCCESS"
    )
    assert (
        client.data.buy_data(
            "ref2", productId="mtn1", phoneNumber="08011112222", network="MTN"
        )["status"]
        == "SUCCESS"
    )
    assert isinstance(
        client.electricity.lookup_meter(disco="enugu", customerId="12345"),
        MeterLookupResult,
    )
    assert (
        client.cable.subscribe_cable_tv(
            "ref3",
            cableTvType="dstv",
            amount=100,
            customerId="12345",
            payerName="Jane Doe",
        )["status"]
        == "SUCCESS"
    )
    assert (
        client.betting.pay_betting(
            "ref4",
            bettingProvider="betnaija",
            amount=100,
            customerId="12345",
            payerName="Jane Doe",
            phoneNumber="08011112222",
        )["status"]
        == "SUCCESS"
    )
