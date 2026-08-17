import pytest

from app.config import Settings, ProviderMode
from app.geocoding.factory import get_geocoder
from app.geocoding.nominatim import NominatimGeocoder
from app.geocoding.paid_stub import PaidGeocoderStub


def test_factory_returns_nominatim_by_default():
    settings = Settings(provider_mode=ProviderMode.FREE)
    assert isinstance(get_geocoder(settings), NominatimGeocoder)


def test_factory_returns_paid_stub_when_mode_is_paid():
    settings = Settings(provider_mode=ProviderMode.PAID)
    assert isinstance(get_geocoder(settings), PaidGeocoderStub)


def test_paid_stub_refuses_to_geocode_instead_of_returning_fixed_coordinates():
    """The stub must fail loudly: silently returning Bogotá for any address would
    produce a polished report describing the wrong city."""
    with pytest.raises(NotImplementedError):
        PaidGeocoderStub().geocode("Carrera 70 # 45-10, Medellín")
