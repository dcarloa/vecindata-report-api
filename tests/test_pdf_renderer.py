from app.pdf_renderer.renderer import render_html, render_pdf

_SAMPLE_REPORT = {
    "address": "Calle 100 # 15-20, Bogotá",
    "map_url": "https://example.com/map.png",
    "satellite_url": "https://example.com/sat.png",
    "pois": {"educacion": [{"name": "Colegio X"}], "salud": []},
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


def test_render_pdf_produces_valid_pdf_bytes():
    pdf_bytes = render_pdf(_SAMPLE_REPORT)
    assert pdf_bytes[:4] == b"%PDF"
