import json
import httpx
import respx
from app.cache import Cache
from app.routing.openrouteservice import OpenRouteServiceRouting, ORS_ISOCHRONES_URL


@respx.mock
def test_isochrones_returns_one_isochrone_per_requested_minute():
    respx.post(ORS_ISOCHRONES_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "features": [
                    {"type": "Feature", "properties": {"value": 300}},
                    {"type": "Feature", "properties": {"value": 600}},
                ]
            },
        )
    )
    routing = OpenRouteServiceRouting(api_key="test-key", client=httpx.Client())
    result = routing.isochrones(lat=4.6097, lon=-74.0817, minutes=[5, 10])

    assert len(result) == 2
    assert result[0].minutes == 5
    assert result[1].minutes == 10


@respx.mock
def test_isochrones_uses_cache_and_skips_second_network_call(tmp_path):
    route = respx.post(ORS_ISOCHRONES_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "features": [
                    {"type": "Feature", "properties": {"value": 300}},
                    {"type": "Feature", "properties": {"value": 600}},
                ]
            },
        )
    )
    cache = Cache(tmp_path)
    routing = OpenRouteServiceRouting(api_key="test-key", client=httpx.Client(), cache=cache)

    routing.isochrones(lat=4.6097, lon=-74.0817, minutes=[5, 10])
    routing.isochrones(lat=4.6097, lon=-74.0817, minutes=[5, 10])

    assert route.call_count == 1


@respx.mock
def test_isochrones_sends_correct_request_payload():
    route = respx.post(ORS_ISOCHRONES_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "features": [
                    {"type": "Feature", "properties": {"value": 300}},
                    {"type": "Feature", "properties": {"value": 600}},
                ]
            },
        )
    )
    routing = OpenRouteServiceRouting(api_key="test-key", client=httpx.Client())
    routing.isochrones(lat=4.6097, lon=-74.0817, minutes=[5, 10])

    # Verify the request was sent
    assert len(route.calls) == 1
    request = route.calls.last.request
    payload = json.loads(request.content)

    # Verify locations are in [lon, lat] order
    assert payload["locations"] == [[-74.0817, 4.6097]]
    # Verify minutes are converted to seconds
    assert payload["range"] == [300, 600]
    # Verify range_type is set correctly
    assert payload["range_type"] == "time"
