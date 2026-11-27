from __future__ import annotations

from dataclasses import dataclass

# Ported from Node's src/types/v1/data/data.types.ts.


@dataclass(frozen=True)
class DataPlan:
    productId: str | None = None
    plan: str | None = None
    amount: float | None = None
