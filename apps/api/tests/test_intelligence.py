from app.intelligence import _metrics_totals, build_recommendations


def test_metrics_totals_maps_headers_and_numeric_values():
    report = {
        "columnHeaders": [{"name": "views"}, {"name": "estimatedMinutesWatched"}],
        "rows": [[120, 45.5]],
    }
    assert _metrics_totals(report) == {"views": 120.0, "estimatedMinutesWatched": 45.5}


def test_recommendations_flag_decline_and_name_top_video():
    result = build_recommendations(
        {"views": 70, "estimatedMinutesWatched": 100},
        {"views": 100},
        [{"title": "A useful tutorial", "views": 40}],
    )
    assert any(item["priority"] == "high" for item in result)
    assert any("A useful tutorial" in item["detail"] for item in result)


def test_recommendations_do_not_invent_trends_without_data():
    result = build_recommendations({}, {}, [])
    assert len(result) == 1
    assert result[0]["priority"] == "info"
