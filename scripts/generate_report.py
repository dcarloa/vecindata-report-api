import json
from app.geocoding.nominatim import NominatimGeocoder
from app.pois.overpass import OverpassPOIProvider
from app.models import Categoria
from app.report_data.orchestrator import build_basic_report

ADDRESS = "Calle 100 # 15-20, Bogotá, Colombia"

if __name__ == "__main__":
    report = build_basic_report(
        address=ADDRESS,
        geocoder=NominatimGeocoder(),
        poi_provider=OverpassPOIProvider(),
        categories=[Categoria.EDUCACION, Categoria.SALUD, Categoria.TRANSPORTE],
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
