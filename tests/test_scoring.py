from app.scoring.scoring import calculate_scores


def test_calculate_scores_with_full_data_at_default_radius_returns_high_scores():
    """At the reference radius (1000m, the default), hitting the new caps
    (60 transporte, 15 parques) still yields a perfect score — the caps
    changed, not the concept of "perfect coverage"."""
    report_data = {
        "pois": {
            "transporte": [{}] * 60,
            "educacion": [{}],
            "salud": [{}],
            "comercio": [{}],
            "restaurantes": [{}],
            "bancos": [{}],
            "parques": [{}] * 15,
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

    Scenario at the default 1000m radius (transport cap 60, park cap 15):
    - 24 transporte POIs -> conectividad = min(24/60, 1.0) x 10 = 4.0
    - 3 service categories -> servicios = 3/5 x 10 = 6.0
    - 0 parques -> areas_verdes = 0.0
    - Expected global_score = round(4.0x0.4 + 6.0x0.4 + 0.0x0.2, 1) = 4.0
    """
    report_data = {
        "pois": {
            "transporte": [{}] * 24,  # conectividad = 4.0
            "educacion": [{}],  # servicios category 1
            "salud": [{}],      # servicios category 2
            "comercio": [{}],   # servicios category 3
            # restaurantes and bancos intentionally omitted
            # parques intentionally omitted -> areas_verdes = 0.0
        }
    }
    result = calculate_scores(report_data)

    sub_score_values = {s.name: s.value for s in result.sub_scores}
    assert sub_score_values["conectividad"] == 4.0
    assert sub_score_values["servicios"] == 6.0
    assert sub_score_values["areas_verdes"] == 0.0
    assert result.global_score == 4.0


def test_calculate_scores_scales_connectivity_and_green_caps_with_radius_area():
    """Regression test: transport-stop and park counts grow with the search
    AREA, not linearly with the radius (confirmed against real Overpass data
    for a dense Bogotá address: 12/38/151 transporte at 500/1000/2000m tracks
    a (radius/1000)^2 curve almost exactly). Without radius-aware caps, the
    same real-world density trivially maxes conectividad/areas_verdes at
    every radius, and choosing a bigger radius always pushes the score toward
    10 — exactly the score-inflation risk visible_categories was designed to
    avoid, now via a different door. The same POI count must score higher at
    a smaller radius (denser relative to what was searched) than at a bigger
    one, because the cap area-scales too.
    """
    pois_with_30_transporte_and_6_parks = {
        "transporte": [{}] * 30,
        "parques": [{}] * 6,
    }

    at_500m = calculate_scores({"pois": pois_with_30_transporte_and_6_parks}, radius_m=500)
    at_1000m = calculate_scores({"pois": pois_with_30_transporte_and_6_parks}, radius_m=1000)
    at_2000m = calculate_scores({"pois": pois_with_30_transporte_and_6_parks}, radius_m=2000)

    conectividad = {
        500: next(s.value for s in at_500m.sub_scores if s.name == "conectividad"),
        1000: next(s.value for s in at_1000m.sub_scores if s.name == "conectividad"),
        2000: next(s.value for s in at_2000m.sub_scores if s.name == "conectividad"),
    }
    areas_verdes = {
        500: next(s.value for s in at_500m.sub_scores if s.name == "areas_verdes"),
        1000: next(s.value for s in at_1000m.sub_scores if s.name == "areas_verdes"),
        2000: next(s.value for s in at_2000m.sub_scores if s.name == "areas_verdes"),
    }

    # 500m: cap = 60*(0.5)^2=15 transporte, 15*(0.5)^2=3.75 parques -> both maxed by 30/6
    assert conectividad[500] == 10.0
    assert areas_verdes[500] == 10.0
    # 1000m: cap = 60 transporte, 15 parques -> 30/60=5.0, 6/15=4.0
    assert conectividad[1000] == 5.0
    assert areas_verdes[1000] == 4.0
    # 2000m: cap = 240 transporte, 60 parques -> 30/240=0.125 -> 1.2, 6/60=1.0
    assert conectividad[2000] == 1.2
    assert areas_verdes[2000] == 1.0

    # The same raw counts must never score *better* at a bigger radius.
    assert conectividad[500] >= conectividad[1000] >= conectividad[2000]
    assert areas_verdes[500] >= areas_verdes[1000] >= areas_verdes[2000]


def test_calculate_scores_keeps_servicios_presence_based_regardless_of_radius():
    """servicios rewards each essential service TYPE existing nearby, not how
    many of each — unlike conectividad/areas_verdes it intentionally does not
    scale with radius."""
    report_data = {
        "pois": {
            "educacion": [{}],
            "salud": [{}],
            "comercio": [{}],
        }
    }
    at_500m = calculate_scores(report_data, radius_m=500)
    at_2000m = calculate_scores(report_data, radius_m=2000)

    servicios_500 = next(s.value for s in at_500m.sub_scores if s.name == "servicios")
    servicios_2000 = next(s.value for s in at_2000m.sub_scores if s.name == "servicios")
    assert servicios_500 == servicios_2000 == 6.0


def test_calculate_scores_defaults_radius_to_1000m_reference():
    """Calling without radius_m (e.g. the CLI dev script) must behave exactly
    like the explicit default (1000m), not an unbounded/zero cap."""
    report_data = {"pois": {"transporte": [{}] * 30}}
    without_radius = calculate_scores(report_data)
    with_explicit_1000 = calculate_scores(report_data, radius_m=1000)

    assert without_radius.global_score == with_explicit_1000.global_score
