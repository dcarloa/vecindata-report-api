from app.models import SubScore, ScoreResult

_WEIGHTS = {
    "conectividad": 0.4,
    "servicios": 0.4,
    "areas_verdes": 0.2,
}


def _score_conectividad(pois: dict) -> float:
    transporte_count = len(pois.get("transporte", []))
    return round(min(transporte_count / 5, 1.0) * 10, 1)


def _score_servicios(pois: dict) -> float:
    categorias = ["educacion", "salud", "comercio", "restaurantes", "bancos"]
    presentes = sum(1 for c in categorias if len(pois.get(c, [])) > 0)
    return round((presentes / len(categorias)) * 10, 1)


def _score_areas_verdes(pois: dict) -> float:
    parques_count = len(pois.get("parques", []))
    return round(min(parques_count / 3, 1.0) * 10, 1)


def calculate_scores(report_data: dict) -> ScoreResult:
    pois = report_data.get("pois", {})
    transporte_count = len(pois.get("transporte", []))
    servicios_categorias = ["educacion", "salud", "comercio", "restaurantes", "bancos"]
    servicios_count = sum(1 for c in servicios_categorias if len(pois.get(c, [])) > 0)
    parques_count = len(pois.get("parques", []))

    sub_scores = [
        SubScore(
            name="conectividad",
            value=_score_conectividad(pois),
            explanation=(
                f"Basado en {transporte_count} parada(s) de transporte encontradas "
                f"en el radio consultado (máximo 5 para puntaje completo)."
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
            value=_score_areas_verdes(pois),
            explanation=(
                f"Basado en {parques_count} parque(s) encontrado(s) en el radio consultado "
                f"(máximo 3 para puntaje completo)."
            ),
        ),
    ]
    global_score = sum(s.value * _WEIGHTS[s.name] for s in sub_scores)
    return ScoreResult(sub_scores=sub_scores, global_score=round(global_score, 1))
