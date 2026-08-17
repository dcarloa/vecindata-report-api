import httpx
import respx
from app.geocoding.nominatim import NominatimGeocoder, NOMINATIM_URL


@respx.mock
def test_geocode_returns_coordinates_from_first_result():
    respx.get(NOMINATIM_URL).mock(
        return_value=httpx.Response(200, json=[{"lat": "4.6097", "lon": "-74.0817"}])
    )
    geocoder = NominatimGeocoder(client=httpx.Client())
    result = geocoder.geocode("Calle 100 # 15-20, Bogotá")
    assert result.lat == 4.6097
    assert result.lon == -74.0817


@respx.mock
def test_geocode_raises_when_address_not_found():
    respx.get(NOMINATIM_URL).mock(return_value=httpx.Response(200, json=[]))
    geocoder = NominatimGeocoder(client=httpx.Client())
    try:
        geocoder.geocode("dirección inexistente")
        assert False, "esperaba ValueError"
    except ValueError:
        pass


@respx.mock
def test_geocode_uses_cache_and_skips_second_network_call(tmp_path):
    from app.cache import Cache

    route = respx.get(NOMINATIM_URL).mock(
        return_value=httpx.Response(200, json=[{"lat": "4.6097", "lon": "-74.0817"}])
    )
    cache = Cache(tmp_path)
    geocoder = NominatimGeocoder(client=httpx.Client(), cache=cache)

    geocoder.geocode("Calle 100 # 15-20, Bogotá")
    geocoder.geocode("Calle 100 # 15-20, Bogotá")

    assert route.call_count == 1
