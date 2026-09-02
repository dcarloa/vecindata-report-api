from app.models import SubScore, ScoreResult

_WEIGHTS = {
    "conectividad": 0.4,
    "servicios": 0.4,
    "areas_verdes": 0.2,
}

# Reference radius the caps below are tuned against. Transport-stop and park
# counts grow with the search AREA, not with the radius itself — confirmed
# against real Overpass data for a dense Bogotá address, where transporte
# counts of 12/38/151 at 500/1000/2000m track a near-exact (radius/1000)^2
# curve. Scaling the caps the same way keeps the score's meaning stable
# across radius choices, instead of letting a bigger radius trivially push
# conectividad/areas_verdes to 10/10 — the same score-inflation concern that
# motivated visible_categories never affecting the score, now closed for the
# radius knob too.
_REFERENCE_RADIUS_M = 1000
_TRANSPORT_CAP_AT_REFERENCE = 60
_PARK_CAP_AT_REFERENCE = 15


def _area_factor(radius_m: int) -> float:
    return (radius_m / _REFERENCE_RADIUS_M) ** 2


def _score_conectividad(pois: dict, radius_m: int) -> float:
    transporte_count = len(pois.get("transporte", []))
    cap = _TRANSPORT_CAP_AT_REFERENCE * _area_factor(radius_m)
    return round(min(transporte_count / cap, 1.0) * 10, 1)


def _score_servicios(pois: dict) -> float:
    # Presence-based by design, not radius-scaled: this rewards each
    # essential service TYPE (educación/salud/comercio/restaurantes/bancos)
    # existing within the search radius, not how many of each — "1 bank
    # nearby" and "40 banks nearby" both mean "there's a bank". Counting
    # harder here would just make the rarest category (bancos, empirically)
    # an arbitrary bottleneck instead of a meaningful signal.
    categorias = ["educacion", "salud", "comercio", "restaurantes", "bancos"]
    presentes = sum(1 for c in categorias if len(pois.get(c, [])) > 0)
    return round((presentes / len(categorias)) * 10, 1)


def _score_areas_verdes(pois: dict, radius_m: int) -> float:
    parques_count = len(pois.get("parques", []))
    cap = _PARK_CAP_AT_REFERENCE * _area_factor(radius_m)
    return round(min(parques_count / cap, 1.0) * 10, 1)


def calculate_scores(report_data: dict, radius_m: int = _REFERENCE_RADIUS_M) -> ScoreResult:
    pois = report_data.get("pois", {})
    transporte_count = len(pois.get("transporte", []))
    servicios_categorias = ["educacion", "salud", "comercio", "restaurantes", "bancos"]
    servicios_count = sum(1 for c in servicios_categorias if len(pois.get(c, [])) > 0)
    parques_count = len(pois.get("parques", []))
    transport_cap = round(_TRANSPORT_CAP_AT_REFERENCE * _area_factor(radius_m))
    park_cap = round(_PARK_CAP_AT_REFERENCE * _area_factor(radius_m))

    sub_scores = [
        SubScore(
            name="conectividad",
            value=_score_conectividad(pois, radius_m),
            explanation=(
                f"Basado en {transporte_count} parada(s) de transporte encontradas "
                f"en el radio consultado (máximo {transport_cap} para puntaje completo)."
            ),
        ),
        SubScore(
            name="servicios",
            value=_score_servicios(pois),
            explanation=(
                f"Basado en {servicios_count} de 5 categorías de servicio (educación, salud, "
                f"comercio, restaurantes, bancos) con al menos un resultado cercano."
            ),
        ),
        SubScore(
            name="areas_verdes",
            value=_score_areas_verdes(pois, radius_m),
            explanation=(
                f"Basado en {parques_count} parque(s) encontrado(s) en el radio consultado "
                f"(máximo {park_cap} para puntaje completo)."
            ),
        ),
    ]
    global_score = sum(s.value * _WEIGHTS[s.name] for s in sub_scores)
    return ScoreResult(sub_scores=sub_scores, global_score=round(global_score, 1))
