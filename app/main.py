import anthropic
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from app.config import settings
from app.cache import Cache
from app.geocoding.factory import get_geocoder
from app.pois.overpass import OverpassPOIProvider
from app.routing.openrouteservice import OpenRouteServiceRouting
from app.staticmap.mapbox import MapboxStaticMapProvider
from app.narrative.narrative import NarrativeGenerator
from app.report_data.full_orchestrator import build_full_report
from app.pdf_renderer.renderer import render_pdf

app = FastAPI(title="VecinData Report API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

_cache = Cache(settings.cache_dir)


class ReportRequest(BaseModel):
    address: str
    logo_url: str | None = None
    # Restricted to a strict 6-digit hex color: brand_color is interpolated raw
    # into a <style> block in the PDF template, and Jinja2 autoescaping does not
    # escape CSS metacharacters. Without this constraint, a crafted value could
    # inject arbitrary CSS and, since rendering runs a real headless Chromium,
    # trigger SSRF against internal services or cloud metadata endpoints.
    brand_color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")


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
def create_report(request: ReportRequest) -> Response:
    report = build_full_report(
        address=request.address,
        geocoder=get_geocoder(settings, cache=_cache),
        poi_provider=OverpassPOIProvider(cache=_cache),
        routing_provider=OpenRouteServiceRouting(api_key=settings.openrouteservice_api_key, cache=_cache),
        staticmap_provider=MapboxStaticMapProvider(access_token=settings.mapbox_access_token),
        narrative_generator=NarrativeGenerator(client=anthropic.Anthropic(api_key=settings.anthropic_api_key)),
    )
    report["logo_url"] = request.logo_url
    report["brand_color"] = request.brand_color
    pdf_bytes = render_pdf(report)
    return Response(content=pdf_bytes, media_type="application/pdf")
