from app.models.api import TimeRangeInput


def test_time_range_resolve_uses_lookback_when_start_missing():
    resolved = TimeRangeInput(lookback_minutes=30).resolve(default_lookback_minutes=60, step="60s")

    assert resolved.step == "60s"
    assert int((resolved.end - resolved.start).total_seconds()) == 1800
