"""
Integration test: real build_full_report output fed into the real renderer.

Every other test in the suite mocks at a boundary — either the orchestrator's
collaborators are faked and the report dict is only inspected as a dict, or the
renderer is handed a hand-written sample dict. Nothing else pipes actual
orchestrator output into the actual template, so a field-name drift between the
two (e.g. renaming report["pois"] or a POI field the template formats) would
pass every other test and only break in production. This test closes that gap:
only the outermost network adapters are faked; the orchestrator, the scoring,
the template and Playwright are all real.
"""
from app.pdf_renderer.renderer import render_html, render_pdf
from app.report_data.full_orchestrator import build_full_report
from tests.test_full_orchestrator import (
    FakeGeocoder,
    FakeNarrativeGenerator,
    FakePOIProvider,
    FakeRoutingProvider,
    FakeStaticMapProvider,
)

_ADDRESS = "Calle 100 # 15-20, Bogotá"
_ALL_CATEGORIES = [
    "educacion",
    "salud",
    "transporte",
    "comercio",
    "restaurantes",
    "parques",
    "bancos",
]


def _build_report() -> dict:
    return build_full_report(
        address=_ADDRESS,
        geocoder=FakeGeocoder(),
        poi_provider=FakePOIProvider(),
        routing_provider=FakeRoutingProvider(),
        staticmap_provider=FakeStaticMapProvider(),
        narrative_generator=FakeNarrativeGenerator(),
    )


def test_orchestrator_output_renders_all_sections_in_html():
    html = render_html(_build_report())

    assert _ADDRESS in html
    for category in _ALL_CATEGORIES:
        assert category in html, f"categoría ausente en el HTML renderizado: {category}"
    for minutes in (5, 10, 15):
        assert f"{minutes} min caminando" in html


def test_orchestrator_output_renders_nearest_distance_for_populated_category():
    html = render_html(_build_report())
    # FakePOIProvider returns one parque at 200 m; the template must format it.
    assert "parques: 1 encontrados (el más cercano a 200 m)" in html


def test_orchestrator_output_renders_to_valid_pdf():
    pdf_bytes = render_pdf(_build_report())
    assert pdf_bytes[:4] == b"%PDF"
