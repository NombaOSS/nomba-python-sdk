from nomba.lib.token_store import MemoryTokenStore, TokenData

TOKEN: TokenData = {
    "businessId": "b",
    "access_token": "abc",
    "refresh_token": "r",
    "expiresAt": "2030-01-01T00:00:00Z",
}


def test_memory_store_round_trip_and_clear():
    store = MemoryTokenStore()
    assert store.get() is None
    store.set(TOKEN)
    assert store.get() == TOKEN
    store.clear()
    assert store.get() is None
