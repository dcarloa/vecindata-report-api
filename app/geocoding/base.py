from typing import Protocol
from app.models import Coordinates


class Geocoder(Protocol):
    def geocode(self, address: str) -> Coordinates: ...
