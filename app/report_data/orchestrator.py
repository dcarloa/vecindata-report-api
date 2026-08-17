from app.geocoding.base import Geocoder
from app.pois.base import POIProvider
from app.models import Categoria


def build_basic_report(
    address: str,
    geocoder: Geocoder,
    poi_provider: POIProvider,
    categories: list[Categoria],
    radius_m: int = 1000,
) -> dict:
    coords = geocoder.geocode(address)
    pois_by_category = {
        category.value: [
            poi.model_dump() for poi in poi_provider.find_pois(coords.lat, coords.lon, category, radius_m)
        ]
        for category in categories
    }
    return {
        "address": address,
        "coordinates": coords.model_dump(),
        "pois": pois_by_category,
    }
