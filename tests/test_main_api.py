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
