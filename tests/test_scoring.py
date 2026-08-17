from app.scoring.scoring import calculate_scores


def test_calculate_scores_with_full_data_returns_high_scores():
    report_data = {
        "pois": {
            "transporte": [{}] * 5,
            "educacion": [{}],
            "salud": [{}],
            "comercio": [{}],
            "restaurantes": [{}],
            "bancos": [{}],
            "parques": [{}] * 3,
        }
    }
    result = calculate_scores(report_data)
    assert result.global_score == 10.0
    names = {s.name for s in result.sub_scores}
    assert names == {"conectividad", "servicios", "areas_verdes"}


def test_calculate_scores_with_no_data_returns_zero():
    result = calculate_scores({"pois": {}})
    assert result.global_score == 0.0
