import sys

import nomba
from nomba import MemoryTokenStore, Nomba, NombaError, verify_signature

expected = sys.argv[1] if len(sys.argv) > 1 else None
if expected is not None:
    assert nomba.__version__ == expected, (nomba.__version__, expected)

client = Nomba(client_id="smoke", client_secret="smoke", account_id="smoke")
assert client.checkout is not None
assert client.transfers is not None
assert issubclass(NombaError, Exception)
assert MemoryTokenStore() is not None
assert verify_signature({}, "invalid", "2025-01-01T00:00:00Z", "secret") is False
print(f"nomba {nomba.__version__} OK")
