import httpx
import respx
from app.models import Categoria
from app.pois.overpass import OverpassPOIProvider, OVERPASS_URL


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
