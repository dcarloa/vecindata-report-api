import re
from typing import Literal

import httpx
from google import genai
from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from app.config import settings
from app.cache import Cache
from app.models import Coordinates
from app.pois.overpass import OverpassPOIProvider
from app.routing.openrouteservice import OpenRouteServiceRouting
from app.staticmap.mapbox import MapboxStaticMapProvider
from app.narrative.narrative import NarrativeGenerator
from app.report_data.full_orchestrator import build_full_report
from app.pdf_renderer.renderer import render_pdf

app = FastAPI(title="VecinData Report API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://vecindata.dcarloabad.workers.dev",
    ],
    allow_methods=["POST"],
    allow_headers=["Content-Type", "X-Operator-Key"],
)

def _whatsapp_link(raw: str | None) -> str | None:
    """A wa.me link only if `raw` plausibly holds a phone number (7-15 digits,
    the E.164 range) — otherwise the template falls back to showing it as
    plain text instead of a broken link."""
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if not 7 <= len(digits) <= 15:
        return None
    return f"https://wa.me/{digits}"


if not settings.operator_access_key:
    print("WARNING: OPERATOR_ACCESS_KEY is not set — POST /reports is publicly accessible with no access control.")

_cache = Cache(settings.cache_dir)


class ReportRequest(BaseModel):
    address: str
    lat: float
    lon: float
    logo_url: str | None = None
    # Restricted to a strict 6-digit hex color: brand_color is interpolated raw
    # into a <style> block in the PDF template, and Jinja2 autoescaping does not
    # escape CSS metacharacters. Without this constraint, a crafted value could
    # inject arbitrary CSS and, since rendering runs a real headless Chromium,
    # trigger SSRF against internal services or cloud metadata endpoints.
    brand_color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    radius_m: Literal[500, 1000, 2000] = 1000
    advisor_name: str | None = None
    advisor_whatsapp: str | None = None
    advisor_email: str | None = None
    tagline: str | None = None


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(httpx.HTTPError)
async def http_error_handler(request: Request, exc: httpx.HTTPError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"detail": "Error al consultar un proveedor de datos externo."},
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/reports")
def create_report(request: ReportRequest, x_operator_key: str | None = Header(default=None)) -> Response:
    if settings.operator_access_key and x_operator_key != settings.operator_access_key:
        return JSONResponse(status_code=401, content={"detail": "Clave de acceso inválida."})
    try:
        report = build_full_report(
            address=request.address,
            coords=Coordinates(lat=request.lat, lon=request.lon),
            poi_provider=OverpassPOIProvider(cache=_cache),
            routing_provider=OpenRouteServiceRouting(api_key=settings.openrouteservice_api_key, cache=_cache),
            staticmap_provider=MapboxStaticMapProvider(access_token=settings.mapbox_access_token),
            narrative_generator=NarrativeGenerator(
                client=genai.Client(vertexai=True, api_key=settings.google_api_key)
            ),
            radius_m=request.radius_m,
        )
        report["logo_url"] = request.logo_url
        report["brand_color"] = request.brand_color
        report["advisor_name"] = request.advisor_name
        report["advisor_whatsapp"] = request.advisor_whatsapp
        report["advisor_whatsapp_link"] = _whatsapp_link(request.advisor_whatsapp)
        report["advisor_email"] = request.advisor_email
        report["tagline"] = request.tagline
        pdf_bytes = render_pdf(report)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except (ValueError, httpx.HTTPError):
        # Handled by the exception_handlers above — both are registered as
        # specific types, so they route through FastAPI's ExceptionMiddleware
        # (inside CORSMiddleware). Re-raise to let that dispatch happen.
        raise
    except Exception:
        # Any other error shape (e.g. the Gemini SDK's own exceptions,
        # Playwright's) — returned directly rather than re-raised, since a
        # handler registered via @app.exception_handler(Exception) would
        # route to Starlette's ServerErrorMiddleware, which sits *outside*
        # CORSMiddleware and would leave the response without CORS headers,
        # making the browser block it entirely.
        return JSONResponse(
            status_code=500,
            content={"detail": "Ocurrió un error inesperado en el servidor."},
        )
