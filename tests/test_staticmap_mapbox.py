from app.staticmap.mapbox import MapboxStaticMapProvider


def test_map_url_includes_coordinates_and_token():
    provider = MapboxStaticMapProvider(access_token="tok123")
    url = provider.map_url(lat=4.6097, lon=-74.0817, zoom=16, width=600, height=400)
    assert "4.6097" in url
    assert "-74.0817" in url
    assert "access_token=tok123" in url
    assert url.startswith("https://api.mapbox.com/styles/v1/mapbox/streets-v12/static/")


def test_satellite_url_uses_satellite_style():
    provider = MapboxStaticMapProvider(access_token="tok123")
    url = provider.satellite_url(lat=4.6097, lon=-74.0817)
    assert "satellite-v9" in url
