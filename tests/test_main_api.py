from unittest.mock import patch

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
