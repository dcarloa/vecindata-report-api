"""
Adaptador SIMULADO para un proveedor de geocodificación de pago (ej. Google Maps).
No hace ninguna llamada de red real: devuelve coordenadas de ejemplo fijas.

No reemplazar esto por una integración real con credenciales de pago sin
confirmarlo explícitamente con el usuario primero (ver design spec, sección 6:
"Regla de costos").
"""
from app.models import Coordinates


class PaidGeocoderStub:
    def geocode(self, address: str) -> Coordinates:
        return Coordinates(lat=4.6097, lon=-74.0817)
