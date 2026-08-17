from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("app.main.render_pdf", return_value=b"%PDF-fake-bytes")
@patch("app.main.build_full_report", return_value={"address": "Calle 100, Bogotá"})
def test_create_report_returns_pdf_response(mock_build, mock_render):
    response = client.post("/reports", json={"address": "Calle 100, Bogotá"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == b"%PDF-fake-bytes"
    mock_build.assert_called_once()
    mock_render.assert_called_once()


@patch(
    "app.main.build_full_report",
    side_effect=ValueError("No se encontraron coordenadas para la dirección: xyz"),
)
def test_address_not_found_returns_422_not_500(mock_build):
    """'Address not found' is the most likely real user error and must surface as a
    client error with a usable message, not an opaque 500."""
    response = client.post("/reports", json={"address": "xyz"})
    assert response.status_code == 422
    assert "No se encontraron coordenadas" in response.json()["detail"]


@patch("app.main.build_full_report", side_effect=httpx.ConnectTimeout("timeout"))
def test_upstream_provider_failure_returns_502(mock_build):
    response = client.post("/reports", json={"address": "Calle 100, Bogotá"})
    assert response.status_code == 502
    assert "proveedor de datos externo" in response.json()["detail"]


@patch("app.main.build_full_report", side_effect=RuntimeError("boom"))
def test_unhandled_exception_returns_500_with_cors_headers(mock_build):
    """A 4th error shape exists beyond ValueError/httpx.HTTPError: the Anthropic/Gemini
    SDK and Playwright can both raise their own exception types. Uncaught, Starlette's
    ServerErrorMiddleware generates the 500 *outside* CORSMiddleware, so the browser
    blocks the response entirely and the operator sees a misleading "can't connect"
    instead of the real error. A catch-all handler routes through FastAPI's own
    ExceptionMiddleware (inside CORSMiddleware), so the header is actually applied."""
    response = client.post(
        "/reports",
        json={"address": "Calle 100, Bogotá"},
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 500
    assert response.json()["detail"] == "Ocurrió un error inesperado en el servidor."
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


@patch("app.main.render_pdf", return_value=b"%PDF-fake-bytes")
@patch("app.main.build_full_report", return_value={"address": "Calle 100, Bogotá"})
def test_create_report_passes_branding_fields_into_report_dict(mock_build, mock_render):
    client.post(
        "/reports",
        json={
            "address": "Calle 100, Bogotá",
            "logo_url": "https://example.com/logo.png",
            "brand_color": "#1a73e8",
        },
    )
    rendered_report = mock_render.call_args[0][0]
    assert rendered_report["logo_url"] == "https://example.com/logo.png"
    assert rendered_report["brand_color"] == "#1a73e8"


@patch("app.main.render_pdf", return_value=b"%PDF-fake-bytes")
@patch("app.main.build_full_report", return_value={"address": "Calle 100, Bogotá"})
def test_create_report_branding_fields_default_to_none(mock_build, mock_render):
    client.post("/reports", json={"address": "Calle 100, Bogotá"})
    rendered_report = mock_render.call_args[0][0]
    assert rendered_report["logo_url"] is None
    assert rendered_report["brand_color"] is None


@patch("app.main.render_pdf")
@patch("app.main.build_full_report")
def test_create_report_rejects_malformed_brand_color(mock_build, mock_render):
    """brand_color is interpolated raw into a <style> block in the PDF template.
    Jinja2 autoescaping does not escape CSS metacharacters, so a value like
    'red; } h1 { background: url(http://evil) } /*' could inject arbitrary CSS
    and, since render_pdf runs a real headless Chromium, trigger SSRF. Only a
    strict 6-digit hex color must be accepted; anything else must 422 before
    the request ever reaches the orchestrator or the renderer."""
    response = client.post(
        "/reports",
        json={
            "address": "Calle 100, Bogotá",
            "brand_color": "red; } h1 { background: url(http://evil) } /*",
        },
    )
    assert response.status_code == 422
    mock_build.assert_not_called()
    mock_render.assert_not_called()


def test_cors_preflight_allows_localhost_dev_origin():
    response = client.options(
        "/reports",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_unlisted_origin():
    response = client.options(
        "/reports",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert "access-control-allow-origin" not in response.headers
