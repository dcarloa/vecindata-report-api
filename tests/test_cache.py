from app.cache import Cache


def test_set_then_get_returns_same_value(tmp_path):
    cache = Cache(tmp_path)
    cache.set("geocoder:some-address", {"lat": 4.6, "lon": -74.0})
    assert cache.get("geocoder:some-address") == {"lat": 4.6, "lon": -74.0}


def test_get_returns_none_for_missing_key(tmp_path):
    cache = Cache(tmp_path)
    assert cache.get("does-not-exist") is None
