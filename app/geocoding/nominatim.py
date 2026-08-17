import httpx
from app.models import Coordinates
from app.cache import Cache

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


class NominatimGeocoder:
    def __init__(
        self,
        client: httpx.Client | None = None,
        cache: Cache | None = None,
        user_agent: str = "vecindata-report-api/0.1",
    ):
        self._client = client or httpx.Client(headers={"User-Agent": user_agent}, timeout=30.0)
        self._cache = cache

    def geocode(self, address: str) -> Coordinates:
        cache_key = f"nominatim:geocode:{address}"
        if self._cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return Coordinates(**cached)

        response = self._client.get(
            NOMINATIM_URL,
            params={"q": address, "format": "json", "limit": 1},
        )
        response.raise_for_status()
        results = response.json()
        if not results:
            raise ValueError(f"No se encontraron coordenadas para la dirección: {address}")

        coords = Coordinates(lat=float(results[0]["lat"]), lon=float(results[0]["lon"]))
        if self._cache:
            self._cache.set(cache_key, coords.model_dump())
        return coords
