from app.pois.base import POIProvider
from app.routing.base import RoutingProvider
from app.staticmap.base import StaticMapProvider
from app.scoring.scoring import calculate_scores
from app.narrative.narrative import NarrativeGenerator, verify_groundedness
from app.models import Categoria, Coordinates

_ALL_CATEGORIES = list(Categoria)
_ISOCHRONE_MINUTES = [5, 10, 15]


def build_full_report(
    address: str,
    coords: Coordinates,
    poi_provider: POIProvider,
    routing_provider: RoutingProvider,
    staticmap_provider: StaticMapProvider,
    narrative_generator: NarrativeGenerator,
    radius_m: int = 1000,
    visible_categories: list[str] | None = None,
) -> dict:
    pois = {
        category.value: [
            poi.model_dump() for poi in poi_provider.find_pois(coords.lat, coords.lon, category, radius_m)
        ]
        for category in _ALL_CATEGORIES
    }

    isochrones = [
        iso.model_dump() for iso in routing_provider.isochrones(coords.lat, coords.lon, _ISOCHRONE_MINUTES)
    ]

    report = {
        "address": address,
        "coordinates": coords.model_dump(),
        "pois": pois,
        "isochrones": isochrones,
        "map_url": staticmap_provider.map_url(coords.lat, coords.lon),
        "satellite_url": staticmap_provider.satellite_url(coords.lat, coords.lon),
    }

    score = calculate_scores(report)
    report["score"] = score.model_dump()

    if visible_categories is not None:
        report["pois"] = {
            cat: items for cat, items in report["pois"].items()
            if cat in visible_categories
        }

    # The narrative generator must only see visible-category data. report["score"]
    # was computed pre-filter (see the Global Constraints in the plan: the score
    # always sees all 7 categories) and each sub-score's `explanation` is a free-text
    # string that can name a hidden category along with its real count (e.g. "Basado
    # en 4 parada(s) de transporte encontradas..." even when transporte is hidden).
    # If the model echoes that, verify_groundedness correctly rejects it against the
    # filtered `pois` dict — but that's a silent, confusing fallback. Strip
    # `explanation` here so the LLM never sees it in the first place; keep only the
    # numeric/label fields it's allowed to describe.
    narrative_payload = {
        "address": report["address"],
        "pois": report["pois"],
        "score": {
            "sub_scores": [
                {"name": sub["name"], "value": sub["value"]}
                for sub in report["score"]["sub_scores"]
            ],
            "global_score": report["score"]["global_score"],
        },
    }
    narrative = narrative_generator.generate(narrative_payload)
    if not verify_groundedness(narrative, narrative_payload):
        narrative = (
            "Resumen no disponible: no se pudo verificar que la descripción generada "
            "se basara únicamente en los datos recolectados."
        )
    report["narrative"] = narrative

    return report
