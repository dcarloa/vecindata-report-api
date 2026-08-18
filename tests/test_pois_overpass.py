import httpx
import respx
from app.models import Categoria
from app.pois.overpass import OverpassPOIProvider, OVERPASS_URL


@respx.mock
def test_default_client_sends_a_user_agent_overpass_will_accept():
    # Overpass's Apache front-end returns a bare 406 (rejected before ever
    # reaching the Overpass app) for requests with no User-Agent — httpx's
    # default "python-httpx/x.x" triggers this every time. That 406 was
    # being silently swallowed by the graceful-degradation except clause
    # below, so every single report showed 0 POIs in every category,
    # regardless of the address. A real User-Agent must be sent by default,
    # the same way NominatimGeocoder already does.
    route = respx.post(OVERPASS_URL).mock(
        return_value=httpx.Response(200, json={"elements": []})
    )
    provider = OverpassPOIProvider()

    provider.find_pois(lat=4.6097, lon=-74.0817, category=Categoria.EDUCACION, radius_m=1000)

    sent_request = route.calls.last.request
    assert "user-agent" in sent_request.headers
    assert "python-httpx" not in sent_request.headers["user-agent"].lower()


@respx.mock
def test_find_pois_returns_sorted_by_distance():
    respx.post(OVERPASS_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "elements": [
                    {"lat": 4.611, "lon": -74.082, "tags": {"name": "Colegio Lejos"}},
                    {"lat": 4.6098, "lon": -74.0818, "tags": {"name": "Colegio Cerca"}},
                ]
            },
        )
    )
    provider = OverpassPOIProvider(client=httpx.Client())
    pois = provider.find_pois(lat=4.6097, lon=-74.0817, category=Categoria.EDUCACION, radius_m=1000)

    assert len(pois) == 2
    assert pois[0].name == "Colegio Cerca"
    assert pois[0].distance_m < pois[1].distance_m


@respx.mock
def test_find_pois_returns_empty_list_when_overpass_is_unreachable():
    # Overpass is a shared public resource that occasionally rate-limits or
    # blocks callers outright (406/429/5xx) — a POI outage should degrade
    # the report (fewer POIs shown) rather than fail the whole request.
    respx.post(OVERPASS_URL).mock(return_value=httpx.Response(406))
    provider = OverpassPOIProvider(client=httpx.Client())

    pois = provider.find_pois(lat=4.6097, lon=-74.0817, category=Categoria.EDUCACION, radius_m=1000)

    assert pois == []


@respx.mock
def test_find_pois_does_not_cache_an_overpass_failure(tmp_path):
    from app.cache import Cache

    cache = Cache(tmp_path)
    route = respx.post(OVERPASS_URL).mock(return_value=httpx.Response(406))
    provider = OverpassPOIProvider(client=httpx.Client(), cache=cache)

    provider.find_pois(lat=4.6097, lon=-74.0817, category=Categoria.EDUCACION, radius_m=1000)
    provider.find_pois(lat=4.6097, lon=-74.0817, category=Categoria.EDUCACION, radius_m=1000)

    # A failure must not be cached as "confirmed zero results" — the second
    # call should retry the network, not silently trust a stale outage.
    assert route.call_count == 2


@respx.mock
def test_find_pois_uses_cache_and_skips_second_network_call(tmp_path):
    from app.cache import Cache

    route = respx.post(OVERPASS_URL).mock(
        return_value=httpx.Response(
            200, json={"elements": [{"lat": 4.61, "lon": -74.08, "tags": {"name": "Colegio"}}]}
        )
    )
    cache = Cache(tmp_path)
    provider = OverpassPOIProvider(client=httpx.Client(), cache=cache)

    provider.find_pois(lat=4.6097, lon=-74.0817, category=Categoria.EDUCACION, radius_m=1000)
    provider.find_pois(lat=4.6097, lon=-74.0817, category=Categoria.EDUCACION, radius_m=1000)

    assert route.call_count == 1


@respx.mock
def test_find_pois_handles_way_elements_with_center_coordinates():
    """Test that way/relation elements with center coordinates are parsed correctly."""
    respx.post(OVERPASS_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "elements": [
                    # Node element (direct lat/lon)
                    {"lat": 4.611, "lon": -74.082, "tags": {"name": "Hospital Pequeño"}},
                    # Way element (center coordinates) - simulating a large polygon like a park or hospital building
                    {
                        "type": "way",
                        "center": {"lat": 4.6105, "lon": -74.0819},
                        "tags": {"name": "Parque Central"},
                    },
                ]
            },
        )
    )
    provider = OverpassPOIProvider(client=httpx.Client())
    pois = provider.find_pois(
        lat=4.6097, lon=-74.0817, category=Categoria.PARQUES, radius_m=1000
    )

    assert len(pois) == 2
    # Verify both node and way elements are included
    names = {poi.name for poi in pois}
    assert "Hospital Pequeño" in names
    assert "Parque Central" in names
    # Verify the way element coordinates were correctly extracted from center
    parque = next(poi for poi in pois if poi.name == "Parque Central")
    assert abs(parque.lat - 4.6105) < 0.0001
    assert abs(parque.lon - (-74.0819)) < 0.0001


@respx.mock
def test_find_pois_skips_elements_without_usable_coordinates():
    """Regression test: way/relation elements occasionally come back without a
    'center' object; those must be skipped, not raise KeyError."""
    respx.post(OVERPASS_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "elements": [
                    {"lat": 4.611, "lon": -74.082, "tags": {"name": "Parque Válido"}},
                    # way with no center at all
                    {"type": "way", "id": 1, "tags": {"name": "Sin Centro"}},
                    # relation with a malformed center
                    {"type": "relation", "id": 2, "center": {}, "tags": {"name": "Centro Vacío"}},
                ]
            },
        )
    )
    provider = OverpassPOIProvider(client=httpx.Client())
    pois = provider.find_pois(
        lat=4.6097, lon=-74.0817, category=Categoria.PARQUES, radius_m=1000
    )

    assert [poi.name for poi in pois] == ["Parque Válido"]
