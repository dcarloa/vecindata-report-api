import httpx
import respx
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
