from app.models import Coordinates, POI, Categoria
from app.report_data.orchestrator import build_basic_report


class FakeGeocoder:
    def geocode(self, address):
        return Coordinates(lat=4.6097, lon=-74.0817)


class FakePOIProvider:
    def find_pois(self, lat, lon, category, radius_m):
        return [POI(name="Ejemplo", category=category, lat=lat, lon=lon, distance_m=100.0)]


def test_build_basic_report_includes_coordinates_and_pois_by_category():
    report = build_basic_report(
        address="Calle 100 # 15-20, Bogotá",
        geocoder=FakeGeocoder(),
        poi_provider=FakePOIProvider(),
        categories=[Categoria.EDUCACION, Categoria.SALUD],
    )
    assert report["coordinates"] == {"lat": 4.6097, "lon": -74.0817}
    assert len(report["pois"]["educacion"]) == 1
    assert len(report["pois"]["salud"]) == 1
