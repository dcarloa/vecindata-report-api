from typing import Protocol
from app.models import POI, Categoria


class POIProvider(Protocol):
    def find_pois(self, lat: float, lon: float, category: Categoria, radius_m: int) -> list[POI]: ...
