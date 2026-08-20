from unittest.mock import MagicMock, patch
from app.pdf_renderer.renderer import render_html, render_pdf

_SAMPLE_REPORT = {
    "address": "Calle 100 # 15-20, Bogotá",
    "map_url": "https://example.com/map.png",
    "satellite_url": "https://example.com/sat.png",
    "pois": {
        "educacion": [
            {"name": "Colegio X", "category": "educacion", "lat": 4.61, "lon": -74.08, "distance_m": 137.4}
        ],
        "salud": [],
    },
    "isochrones": [{"minutes": 5, "geojson": {}}, {"minutes": 10, "geojson": {}}],
    "score": {
        "global_score": 8.5,
        "sub_scores": [{"name": "conectividad", "value": 9.0, "explanation": "Buena cobertura de transporte."}],
    },
    "narrative": "Zona bien conectada con acceso a transporte público.",
}


def test_render_html_includes_address_narrative_and_isochrones():
    html = render_html(_SAMPLE_REPORT)
    assert "Calle 100 # 15-20, Bogotá" in html
    assert "Zona bien conectada" in html
    assert "10 min caminando" in html


def test_render_html_includes_count_and_distance_to_nearest_poi():
    html = render_html(_SAMPLE_REPORT)
    assert "educacion: 1 encontrados (el más cercano a 137 m)" in html
    # Categories with no results show the count only, with no distance clause.
    assert "salud: 0 encontrados</li>" in html


def test_render_html_escapes_user_controlled_input():
    """Regression test: unescaped input would execute inside the headless Chromium
    instance that render_pdf loads the HTML into."""
    report = {**_SAMPLE_REPORT, "address": "<script>alert(1)</script>Calle 100"}
    html = render_html(report)
    assert "&lt;script&gt;" in html
    assert "<script>" not in html


def test_render_pdf_produces_valid_pdf_bytes():
    pdf_bytes = render_pdf(_SAMPLE_REPORT)
    assert pdf_bytes[:4] == b"%PDF"


def test_render_pdf_closes_browser_even_on_pdf_failure():
    """Regression test: verify browser.close() is called in finally block even when page.pdf() raises."""
    with patch("app.pdf_renderer.renderer.sync_playwright") as mock_sync_playwright:
        # Setup mock Playwright context manager and browser
        mock_playwright_instance = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()

        # Configure the context manager chain
        mock_sync_playwright.return_value.__enter__ = MagicMock(
            return_value=mock_playwright_instance
        )
        mock_sync_playwright.return_value.__exit__ = MagicMock(return_value=None)

        # Setup chromium.launch() to return our mock browser
        mock_playwright_instance.chromium.launch.return_value = mock_browser

        # Setup browser.new_page() to return our mock page
        mock_browser.new_page.return_value = mock_page

        # Simulate page.pdf() raising an exception
        mock_page.pdf.side_effect = RuntimeError("Simulated PDF generation failure")

        # Verify render_pdf re-raises the exception and still calls browser.close()
        try:
            render_pdf(_SAMPLE_REPORT)
            assert False, "Expected RuntimeError to be raised"
        except RuntimeError as e:
            assert str(e) == "Simulated PDF generation failure"
            # Verify browser.close() was called despite the exception
            mock_browser.close.assert_called_once()


def test_render_html_shows_logo_when_provided():
    report = {**_SAMPLE_REPORT, "logo_url": "https://example.com/logo.png", "brand_color": "#1a73e8"}
    html = render_html(report)
    assert '<img src="https://example.com/logo.png"' in html
    assert "#1a73e8" in html


def test_render_html_omits_logo_when_not_provided():
    report = {**_SAMPLE_REPORT, "logo_url": None, "brand_color": None}
    html = render_html(report)
    assert "<img" not in html.split("<h1>")[0]


def test_render_html_shows_advisor_contact_and_tagline_when_provided():
    report = {
        **_SAMPLE_REPORT,
        "advisor_name": "Ana Torres",
        "advisor_whatsapp": "+57 300 123 4567",
        "advisor_whatsapp_link": "https://wa.me/573001234567",
        "advisor_email": "ana@example.com",
        "tagline": "Presentado por Inmobiliaria XYZ",
    }
    html = render_html(report)
    assert "Ana Torres" in html
    assert '<a href="https://wa.me/573001234567">+57 300 123 4567</a>' in html
    assert '<a href="mailto:ana@example.com">ana@example.com</a>' in html
    assert "Presentado por Inmobiliaria XYZ" in html


def test_render_html_falls_back_to_plain_text_when_whatsapp_has_no_link():
    report = {
        **_SAMPLE_REPORT,
        "advisor_whatsapp": "no-es-un-numero",
        "advisor_whatsapp_link": None,
    }
    html = render_html(report)
    assert "no-es-un-numero" in html
    assert "wa.me" not in html


def test_render_html_omits_advisor_block_when_not_provided():
    html = render_html(_SAMPLE_REPORT)
    # "advisor" still appears in the <style> block's class names — check the
    # actual markup, not the CSS, for absence.
    assert '<div class="advisor">' not in html
    assert '<p class="tagline">' not in html
