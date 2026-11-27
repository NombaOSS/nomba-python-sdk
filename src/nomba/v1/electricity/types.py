from __future__ import annotations

from dataclasses import dataclass

# Ported from Node's src/types/v1/electricity/electricity.types.ts.


@dataclass(frozen=True)
class ElectricityProvider:
    id: str | None = None
    name: str | None = None
