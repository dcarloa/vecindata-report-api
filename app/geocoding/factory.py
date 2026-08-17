from app.config import Settings, ProviderMode
from app.geocoding.base import Geocoder
from app.geocoding.nominatim import NominatimGeocoder
from app.geocoding.paid_stub import PaidGeocoderStub
from app.cache import Cache


def get_geocoder(settings: Settings, cache: Cache | None = None) -> Geocoder:
    if settings.provider_mode == ProviderMode.PAID:
        return PaidGeocoderStub()
    return NominatimGeocoder(cache=cache)
