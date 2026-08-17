from typing import Protocol
from app.models import Isochrone


class RoutingProvider(Protocol):
    def isochrones(self, lat: float, lon: float, minutes: list[int]) -> list[Isochrone]: ...
