from app.pois.base import POIProvider
from app.routing.base import RoutingProvider
from app.staticmap.base import StaticMapProvider
from app.scoring.scoring import calculate_scores
from app.narrative.narrative import NarrativeGenerator, verify_groundedness
from app.models import Categoria, Coordinates

_ALL_CATEGORIES = list(Categoria)
_ISOCHRONE_MINUTES = [5, 10, 15]
_POI_RADIUS_M = 1000


def build_full_report(
    address: str,
    coords: Coordinates,
    poi_provider: POIProvider,
    routing_provider: RoutingProvider,
    staticmap_provider: StaticMapProvider,
    narrative_generator: NarrativeGenerator,
) -> dict:
    pois = {
        category.value: [
            poi.model_dump() for poi in poi_provider.find_pois(coords.lat, coords.lon, category, _POI_RADIUS_M)
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

    narrative_payload = {
        "address": report["address"],
        "pois": report["pois"],
        "score": report["score"],
    }
    narrative = narrative_generator.generate(narrative_payload)
    if not verify_groundedness(narrative, narrative_payload):
        narrative = (
            "Resumen no disponible: no se pudo verificar que la descripción generada "
            "se basara únicamente en los datos recolectados."
        )
    report["narrative"] = narrative

    return report
