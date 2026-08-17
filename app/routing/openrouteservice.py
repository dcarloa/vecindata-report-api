import httpx
from app.models import Isochrone
from app.cache import Cache

ORS_ISOCHRONES_URL = "https://api.openrouteservice.org/v2/isochrones/foot-walking"


class OpenRouteServiceRouting:
    def __init__(self, api_key: str, client: httpx.Client | None = None, cache: Cache | None = None):
        self._api_key = api_key
        self._client = client or httpx.Client(timeout=30.0)
        self._cache = cache

    def isochrones(self, lat: float, lon: float, minutes: list[int]) -> list[Isochrone]:
        cache_key = f"ors:isochrones:{round(lat, 4)}:{round(lon, 4)}:{minutes}"
        if self._cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return [Isochrone(**item) for item in cached]

        response = self._client.post(
            ORS_ISOCHRONES_URL,
            headers={"Authorization": self._api_key},
            json={"locations": [[lon, lat]], "range": [m * 60 for m in minutes], "range_type": "time"},
        )
        response.raise_for_status()
        features = response.json()["features"]
        result = [Isochrone(minutes=m, geojson=feature) for m, feature in zip(minutes, features)]

        if self._cache:
            self._cache.set(cache_key, [iso.model_dump() for iso in result])

        return result
