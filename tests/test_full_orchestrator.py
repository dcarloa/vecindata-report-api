from app.models import Coordinates, POI, Isochrone, Categoria
from app.report_data.full_orchestrator import build_full_report


class FakeGeocoder:
    def geocode(self, address):
        return Coordinates(lat=4.6097, lon=-74.0817)


class FakePOIProvider:
    def find_pois(self, lat, lon, category, radius_m):
        if category == Categoria.PARQUES:
            return [POI(name="Parque Central", category=category, lat=lat, lon=lon, distance_m=200.0)]
        return []


class FakeRoutingProvider:
    def isochrones(self, lat, lon, minutes):
        return [Isochrone(minutes=m, geojson={}) for m in minutes]


class FakeStaticMapProvider:
    def map_url(self, lat, lon, **kwargs):
        return "https://example.com/map.png"

    def satellite_url(self, lat, lon, **kwargs):
        return "https://example.com/sat.png"


class FakeNarrativeGenerator:
    def generate(self, report_data):
        return "La zona cuenta con un parque cercano."


def test_build_full_report_includes_all_sections():
    report = build_full_report(
        address="Calle 100 # 15-20, Bogotá",
        geocoder=FakeGeocoder(),
        poi_provider=FakePOIProvider(),
        routing_provider=FakeRoutingProvider(),
        staticmap_provider=FakeStaticMapProvider(),
        narrative_generator=FakeNarrativeGenerator(),
    )
    assert report["address"] == "Calle 100 # 15-20, Bogotá"
    assert len(report["isochrones"]) == 3
    assert report["score"]["global_score"] >= 0
    assert report["narrative"] == "La zona cuenta con un parque cercano."


def test_build_full_report_replaces_ungrounded_narrative():
    class UngroundedNarrativeGenerator:
        def generate(self, report_data):
            return "Cerca hay un hospital de alta calidad."

    report = build_full_report(
        address="Calle 100 # 15-20, Bogotá",
        geocoder=FakeGeocoder(),
        poi_provider=FakePOIProvider(),
        routing_provider=FakeRoutingProvider(),
        staticmap_provider=FakeStaticMapProvider(),
        narrative_generator=UngroundedNarrativeGenerator(),
    )
    assert "no se pudo verificar" in report["narrative"]
