"""
Adaptador SIMULADO para un proveedor de geocodificación de pago (ej. Google Maps).

Este stub existe únicamente para documentar el punto de extensión (ver
PROVIDER_MODE en app/config.py) — NO debe usarse para generar reportes reales.
Antes de reemplazar esto por una integración real con credenciales de pago,
confirmarlo explícitamente con el usuario primero (ver design spec, sección 6:
"Regla de costos").
"""
from app.models import Coordinates


class PaidGeocoderStub:
    def geocode(self, address: str) -> Coordinates:
        raise NotImplementedError(
            "PROVIDER_MODE=paid no tiene una integración real todavía — este es "
            "un punto de extensión documentado, no un modo utilizable. Activar un "
            "proveedor de pago real requiere confirmarlo explícitamente con el "
            "usuario antes de implementarlo."
        )
