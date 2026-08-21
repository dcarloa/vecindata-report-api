from app.models import Coordinates, POI, Isochrone, Categoria
from app.report_data.full_orchestrator import build_full_report

FAKE_COORDS = Coordinates(lat=4.6097, lon=-74.0817)


def test_build_full_report_passes_radius_to_every_poi_lookup():
    calls = []

    class SpyPOIProvider:
        def find_pois(self, lat, lon, category, radius_m):
            calls.append((category, radius_m))
            return []

    build_full_report(
        address="Calle 100 # 15-20, Bogotá",
        coords=FAKE_COORDS,
        poi_provider=SpyPOIProvider(),
        routing_provider=FakeRoutingProvider(),
        staticmap_provider=FakeStaticMapProvider(),
        narrative_generator=FakeNarrativeGenerator(),
        radius_m=500,
    )

    assert len(calls) == 7
    assert all(radius_m == 500 for _category, radius_m in calls)


def test_build_full_report_defaults_radius_to_1000():
    calls = []

    class SpyPOIProvider:
        def find_pois(self, lat, lon, category, radius_m):
            calls.append(radius_m)
            return []

    build_full_report(
        address="Calle 100 # 15-20, Bogotá",
        coords=FAKE_COORDS,
        poi_provider=SpyPOIProvider(),
        routing_provider=FakeRoutingProvider(),
        staticmap_provider=FakeStaticMapProvider(),
        narrative_generator=FakeNarrativeGenerator(),
    )

    assert all(radius_m == 1000 for radius_m in calls)


class FakePOIProvider:
    def find_pois(self, lat, lon, category, radius_m):
        if category == Categoria.PARQUES:
            return [POI(name="Parque Central", category=category, lat=lat, lon=lon, distance_m=200.0)]
        return []


class MultipleCategoriesFakePOIProvider:
    """Returns non-empty POI data for multiple categories to enable stronger test assertions."""
    def find_pois(self, lat, lon, category, radius_m):
        if category == Categoria.PARQUES:
            return [POI(name="Parque Central", category=category, lat=lat, lon=lon, distance_m=200.0)]
        elif category == Categoria.TRANSPORTE:
            return [
                POI(name="Estación Metro Calle 100", category=category, lat=lat, lon=lon, distance_m=150.0),
                POI(name="Ciclovía", category=category, lat=lat, lon=lon, distance_m=300.0),
            ]
        return []


class FakeRoutingProvider:
    def isochrones(self, lat, lon, minutes):
        return [Isochrone(minutes=m, geojson={}) for m in minutes]


class FakeStaticMapProvider:
    def map_url(self, lat, lon, **kwargs):
        return "https://example.com/map.png?access_token=SECRET_TOKEN"

    def satellite_url(self, lat, lon, **kwargs):
        return "https://example.com/sat.png?access_token=SECRET_TOKEN"


class FakeNarrativeGenerator:
    def generate(self, report_data):
        return "La zona cuenta con un parque cercano."


def test_build_full_report_includes_all_sections():
    report = build_full_report(
        address="Calle 100 # 15-20, Bogotá",
        coords=FAKE_COORDS,
        poi_provider=FakePOIProvider(),
        routing_provider=FakeRoutingProvider(),
        staticmap_provider=FakeStaticMapProvider(),
        narrative_generator=FakeNarrativeGenerator(),
    )
    assert report["address"] == "Calle 100 # 15-20, Bogotá"
    assert len(report["isochrones"]) == 3
    assert report["score"]["global_score"] >= 0
    assert report["narrative"] == "La zona cuenta con un parque cercano."


def test_build_full_report_replaces_ungrounded_narrative():
    class UngroundedNarrativeGenerator:
        def generate(self, report_data):
            return "Cerca hay un hospital de alta calidad."

    report = build_full_report(
        address="Calle 100 # 15-20, Bogotá",
        coords=FAKE_COORDS,
        poi_provider=FakePOIProvider(),
        routing_provider=FakeRoutingProvider(),
        staticmap_provider=FakeStaticMapProvider(),
        narrative_generator=UngroundedNarrativeGenerator(),
    )
    assert "no se pudo verificar" in report["narrative"]


def test_narrative_payload_excludes_map_tokens_and_isochrone_geojson():
    """Regression test: the payload sent to the LLM must not carry the Mapbox
    access token (embedded in the map URLs) nor the bulky, unused isochrone
    GeoJSON — only what the narrative prompt actually describes."""
    captured = {}

    class CapturingNarrativeGenerator:
        def generate(self, report_data):
            captured.update(report_data)
            return "La zona cuenta con un parque cercano."

    build_full_report(
        address="Calle 100 # 15-20, Bogotá",
        coords=FAKE_COORDS,
        poi_provider=FakePOIProvider(),
        routing_provider=FakeRoutingProvider(),
        staticmap_provider=FakeStaticMapProvider(),
        narrative_generator=CapturingNarrativeGenerator(),
    )

    assert set(captured) == {"address", "pois", "score"}
    assert "SECRET_TOKEN" not in str(captured)


def test_build_full_report_hides_non_visible_categories_from_output():
    report = build_full_report(
        address="Calle 100 # 15-20, Bogotá",
        coords=FAKE_COORDS,
        poi_provider=FakePOIProvider(),
        routing_provider=FakeRoutingProvider(),
        staticmap_provider=FakeStaticMapProvider(),
        narrative_generator=FakeNarrativeGenerator(),
        visible_categories=["parques"],
    )
    assert list(report["pois"].keys()) == ["parques"]


def test_build_full_report_score_is_identical_regardless_of_visible_categories():
    """Verify that score is computed from all categories BEFORE filtering.

    Uses a POI provider with multiple non-empty categories (parques, transporte).
    Filters to show only parques (hiding transporte which has real data).
    If the implementation incorrectly filtered before scoring, removing transporte's POIs
    would change the transporte sub-score, causing the test to fail.
    """
    kwargs = dict(
        address="Calle 100 # 15-20, Bogotá",
        coords=FAKE_COORDS,
        poi_provider=MultipleCategoriesFakePOIProvider(),
        routing_provider=FakeRoutingProvider(),
        staticmap_provider=FakeStaticMapProvider(),
        narrative_generator=FakeNarrativeGenerator(),
    )
    full = build_full_report(**kwargs, visible_categories=None)
    filtered = build_full_report(**kwargs, visible_categories=["parques"])

    assert full["score"] == filtered["score"]


def test_build_full_report_narrative_payload_only_sees_visible_categories():
    seen_pois = {}

    class SpyNarrativeGenerator:
        def generate(self, report_data):
            seen_pois.update(report_data["pois"])
            return "resumen"

    build_full_report(
        address="Calle 100 # 15-20, Bogotá",
        coords=FAKE_COORDS,
        poi_provider=FakePOIProvider(),
        routing_provider=FakeRoutingProvider(),
        staticmap_provider=FakeStaticMapProvider(),
        narrative_generator=SpyNarrativeGenerator(),
        visible_categories=["parques"],
    )
    assert list(seen_pois.keys()) == ["parques"]


def test_build_full_report_narrative_payload_score_excludes_explanations():
    """Regression test: score explanations are generated pre-filter and can name a
    hidden category along with its real count (e.g. "Basado en 4 parada(s) de
    transporte encontradas..." even when transporte is hidden). If the narrative
    model echoes that text, verify_groundedness correctly rejects it against the
    filtered `pois` dict and the narrative silently falls back to "Resumen no
    disponible" — so `explanation` must never reach the narrative payload at all.

    Uses MultipleCategoriesFakePOIProvider so the hidden category (transporte) has
    real POI data and therefore a real, non-generic explanation string naming it.
    """
    captured_score = {}

    class SpyNarrativeGenerator:
        def generate(self, report_data):
            captured_score.update(report_data["score"])
            return "resumen"

    build_full_report(
        address="Calle 100 # 15-20, Bogotá",
        coords=FAKE_COORDS,
        poi_provider=MultipleCategoriesFakePOIProvider(),
        routing_provider=FakeRoutingProvider(),
        staticmap_provider=FakeStaticMapProvider(),
        narrative_generator=SpyNarrativeGenerator(),
        visible_categories=["parques"],
    )

    assert "global_score" in captured_score
    assert "sub_scores" in captured_score
    for sub_score in captured_score["sub_scores"]:
        assert set(sub_score.keys()) == {"name", "value"}
        assert "explanation" not in sub_score
    assert "transporte" not in str(captured_score)
