from datetime import UTC, datetime

from powersnitch_app.core.conditions import build_alert_text, evaluate_conditions
from powersnitch_app.models import DeviceSnapshot


def test_evaluate_conditions_thresholds_and_flags():
    snapshot = DeviceSnapshot(
        identifier="ups@localhost",
        observed_at=datetime.now(UTC),
        status_flags={"OB", "LB"},
        battery_charge=19.0,
        runtime_seconds=240.0,
        input_voltage=120.0,
        output_voltage=118.0,
        load_percent=42.0,
        raw_data={"ups.status": "OB LB"},
        is_reachable=True,
    )
    results = {item.key: item for item in evaluate_conditions(snapshot, 25, 300)}
    assert results["on_battery"].active is True
    assert results["low_battery"].active is True
    assert results["battery_low_pct"].active is True
    assert results["runtime_low"].active is True
    assert results["ups_communication_lost"].active is False


def test_build_alert_text_appends_extra_text():
    snapshot = DeviceSnapshot(
        identifier="ups@localhost",
        observed_at=datetime.now(UTC),
        status_flags={"OL"},
        battery_charge=100.0,
        runtime_seconds=1800.0,
        input_voltage=121.0,
        output_voltage=120.0,
        load_percent=24.0,
        raw_data={},
        is_reachable=True,
    )
    subject, body = build_alert_text("Lab UPS", "on_line", "recovered", snapshot, "Check generator log.")
    assert "Lab UPS" in subject
    assert "Check generator log." in body
    assert "State: recovered" in body
