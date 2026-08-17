from app.models import SubScore, ScoreResult

_WEIGHTS = {
    "conectividad": 0.4,
    "servicios": 0.4,
    "areas_verdes": 0.2,
}


def _score_conectividad(pois: dict) -> float:
    transporte_count = len(pois.get("transporte", []))
    return min(transporte_count / 5, 1.0) * 10


def _score_servicios(pois: dict) -> float:
    categorias = ["educacion", "salud", "comercio", "restaurantes", "bancos"]
    presentes = sum(1 for c in categorias if len(pois.get(c, [])) > 0)
    return (presentes / len(categorias)) * 10


def _score_areas_verdes(pois: dict) -> float:
    parques_count = len(pois.get("parques", []))
    return min(parques_count / 3, 1.0) * 10


def calculate_scores(report_data: dict) -> ScoreResult:
    pois = report_data.get("pois", {})
    sub_scores = [
        SubScore(
            name="conectividad",
            value=_score_conectividad(pois),
            explanation="Basado en cantidad de paradas de transporte en el radio consultado.",
        ),
        SubScore(
            name="servicios",
            value=_score_servicios(pois),
            explanation=(
                "Basado en cuántas categorías de servicio (educación, salud, comercio, "
                "restaurantes, bancos) tienen al menos un resultado cercano."
            ),
        ),
        SubScore(
            name="areas_verdes",
            value=_score_areas_verdes(pois),
            explanation="Basado en cantidad de parques encontrados en el radio consultado.",
        ),
    ]
    global_score = sum(s.value * _WEIGHTS[s.name] for s in sub_scores)
    return ScoreResult(sub_scores=sub_scores, global_score=round(global_score, 1))
