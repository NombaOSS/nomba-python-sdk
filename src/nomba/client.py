"""The ``Nomba`` client — the SDK's composition root.

Builds one :class:`~nomba.http.HttpClient` and attaches it to one object
per product domain, mirroring the Node SDK's ``Nomba`` class
(``src/nomba.ts``): ``nomba.accounts``, ``nomba.transfers``, etc.
"""

from __future__ import annotations

from typing import Any

from nomba.http import HttpClient
from nomba.lib.token_store import TokenData
from nomba.v1.accounts import Accounts
from nomba.v1.betting import BillBetting
from nomba.v1.cable import BillCable
from nomba.v1.charge import Charge
from nomba.v1.checkout import Checkout
from nomba.v1.data import BillData
from nomba.v1.direct_debits import DirectDebits
from nomba.v1.electricity import BillElectricity
from nomba.v1.globals.collections import Collections
from nomba.v1.globals.payouts import Payouts
from nomba.v1.requery import Requery
from nomba.v1.terminals import Terminals
from nomba.v1.transactions import Transactions
from nomba.v1.virtual_accounts import VirtualAccounts
from nomba.v1.webhooks import Webhooks
from nomba.v2.airtime import Airtime
from nomba.v2.betting import Betting
from nomba.v2.cable import Cable
from nomba.v2.data import Data
from nomba.v2.electricity import Electricity
from nomba.v2.transfers import Transfers


class Nomba:
    """The Nomba API client.

    Each product domain is exposed as an attribute, e.g.
    ``client.transfers.bank_transfer(...)`` or
    ``client.accounts.get_parent_account()``. See the README for one
    example per usage pattern (plain reads, money-moving calls, webhooks,
    pagination).

    Args:
        client_id: OAuth2 client id issued by Nomba.
        client_secret: OAuth2 client secret issued by Nomba.
        account_id: The merchant account this client acts on behalf of.
        environment: ``"production"`` (default) or ``"sandbox"`` — selects
            the API base URL.
        **options: Node's ``NombaOptions``: ``token_store``, ``on_store_error``,
            ``timeout_s``, ``max_attempts``, ``retry_delay_s``, ``on_request``,
            ``on_response``, ``on_outcome``. See :class:`~nomba.http.HttpClient`.
        http_client: Supply a pre-built :class:`~nomba.http.HttpClient`
            instead of letting ``Nomba`` construct one — mainly a test seam
            (e.g. to inject a mock transport); real callers should leave
            this unset.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        account_id: str,
        environment: str = "production",
        *,
        http_client: HttpClient | None = None,
        **options: Any,
    ) -> None:
        # options: token_store, on_store_error, timeout_s, max_attempts, retry_delay_s,
        # on_request, on_response, on_outcome (Node's NombaOptions).
        self._http = http_client or HttpClient(
            client_id, client_secret, account_id, environment, **options
        )
        self.accounts = Accounts(self._http)
        self.transactions = Transactions(self._http)
        self.virtual_accounts = VirtualAccounts(self._http)
        self.requery = Requery(self._http)
        self.terminals = Terminals(self._http)
        self.checkout = Checkout(self._http)
        self.transfers = Transfers(self._http)
        self.charge = Charge(self._http)
        self.direct_debits = DirectDebits(self._http)
        self.collections = Collections(self._http)
        self.payouts = Payouts(self._http)
        self.bill_electricity = BillElectricity(self._http)
        self.bill_cable = BillCable(self._http)
        self.bill_betting = BillBetting(self._http)
        self.bill_data = BillData(self._http)
        self.airtime = Airtime(self._http)
        self.data = Data(self._http)
        self.electricity = Electricity(self._http)
        self.cable = Cable(self._http)
        self.betting = Betting(self._http)
        self.webhooks = Webhooks(self._http)

    @property
    def environment(self) -> str:
        """``"production"`` or ``"sandbox"``, as passed to the constructor."""
        return self._http.environment

    def issue_token(self) -> TokenData:
        """``POST /v1/auth/token/issue``. Called for you on first use."""
        return self._http.issue_token()

    def refresh_token(self) -> TokenData:
        """``POST /v1/auth/token/refresh``. Called for you 5 minutes before expiry."""
        return self._http.refresh_token()

    def revoke_token(self) -> None:
        """``POST /v1/auth/token/revoke``. Ends the session, e.g. on shutdown."""
        self._http.revoke_token()

    def request(self, method: str, path: str, **options: Any) -> Any:
        """Authenticated call to any Nomba endpoint, including ones without a dedicated
        method. ``options`` are those of :meth:`nomba.http.HttpClient.request`."""
        return self._http.request(method, path, **options)
