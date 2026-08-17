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


def test_calculate_scores_with_mixed_values_validates_weights():
    """Test with distinct sub-score values to verify weighting (0.4/0.4/0.2).

    This test constructs POI data that produces three different non-degenerate
    sub-scores, ensuring the weights themselves are correct. Any buggy weighting
    (e.g. swapped or incorrect values) would fail this test.

    Scenario:
    - 2 transporte POIs → conectividad = min(2/5, 1.0) × 10 = 4.0
    - 3 service categories → servicios = 3/5 × 10 = 6.0
    - 0 parques → areas_verdes = min(0/3, 1.0) × 10 = 0.0
    - Expected global_score = round(4.0×0.4 + 6.0×0.4 + 0.0×0.2, 1)
                            = round(1.6 + 2.4 + 0, 1) = 4.0
    """
    report_data = {
        "pois": {
            "transporte": [{}] * 2,  # conectividad = 4.0
            "educacion": [{}],  # servicios category 1
            "salud": [{}],      # servicios category 2
            "comercio": [{}],   # servicios category 3
            # restaurantes and bancos intentionally omitted
            # parques intentionally omitted → areas_verdes = 0.0
        }
    }
    result = calculate_scores(report_data)

    # Verify all three sub-scores have distinct values
    sub_score_values = {s.name: s.value for s in result.sub_scores}
    assert sub_score_values["conectividad"] == 4.0
    assert sub_score_values["servicios"] == 6.0
    assert sub_score_values["areas_verdes"] == 0.0

    # Verify global score matches the exact weighted calculation
    assert result.global_score == 4.0
