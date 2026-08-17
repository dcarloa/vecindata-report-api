import math
import httpx
from app.models import POI, Categoria
from app.cache import Cache

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

_CATEGORY_TAGS: dict[Categoria, list[tuple[str, str]]] = {
    Categoria.EDUCACION: [("amenity", "school"), ("amenity", "university")],
    Categoria.SALUD: [("amenity", "hospital"), ("amenity", "clinic"), ("amenity", "pharmacy")],
    Categoria.TRANSPORTE: [("highway", "bus_stop"), ("railway", "station")],
    Categoria.COMERCIO: [("shop", "supermarket"), ("shop", "mall")],
    Categoria.RESTAURANTES: [("amenity", "restaurant"), ("amenity", "cafe")],
    Categoria.PARQUES: [("leisure", "park")],
    Categoria.BANCOS: [("amenity", "bank")],
}


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _get_lat(element: dict) -> float:
    """Extract latitude from node (direct) or way/relation (from center) element."""
    if "lat" in element:
        return element["lat"]
    return element["center"]["lat"]


def _get_lon(element: dict) -> float:
    """Extract longitude from node (direct) or way/relation (from center) element."""
    if "lon" in element:
        return element["lon"]
    return element["center"]["lon"]


class OverpassPOIProvider:
    def __init__(self, client: httpx.Client | None = None, cache: Cache | None = None):
        self._client = client or httpx.Client(timeout=30.0)
        self._cache = cache

    def find_pois(self, lat: float, lon: float, category: Categoria, radius_m: int) -> list[POI]:
        cache_key = f"overpass:{category.value}:{round(lat, 4)}:{round(lon, 4)}:{radius_m}"
        if self._cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return [POI(**item) for item in cached]

        tags = _CATEGORY_TAGS[category]
        clauses = "".join(
            f'nwr["{key}"="{value}"](around:{radius_m},{lat},{lon});' for key, value in tags
        )
        query = f"[out:json];({clauses});out center;"

        response = self._client.post(OVERPASS_URL, data={"data": query})
        response.raise_for_status()
        elements = response.json().get("elements", [])

        pois = sorted(
            (
                POI(
                    name=el.get("tags", {}).get("name", "Sin nombre"),
                    category=category,
                    lat=_get_lat(el),
                    lon=_get_lon(el),
                    distance_m=_haversine_m(lat, lon, _get_lat(el), _get_lon(el)),
                )
                for el in elements
            ),
            key=lambda p: p.distance_m,
        )

        if self._cache:
            self._cache.set(cache_key, [poi.model_dump() for poi in pois])

        return pois
