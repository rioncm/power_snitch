from pathlib import Path

from powersnitch_app.integrations.nut import parse_upsc, snapshot_from_status


def test_parse_upsc_fixture():
    raw = Path("devplans/ups_dummies/Tripp_Lite__SMC15002URM__usbhid-ups__2.7.4__01.dev").read_text(
        encoding="utf-8"
    )
    parsed = parse_upsc(raw)
    assert parsed["ups.status"] == "OL"
    assert parsed["battery.charge"] == "100"
    assert parsed["device.model"] == "TRIPP LITE SMC15002URM"


def test_snapshot_from_status_extracts_flags_and_metrics():
    status = {
        "ups.status": "OB LB",
        "battery.charge": "14",
        "battery.runtime": "125",
        "input.voltage": "119.2",
        "output.voltage": "117.8",
        "ups.load": "53",
    }
    snapshot = snapshot_from_status("ups@localhost", status)
    assert snapshot.identifier == "ups@localhost"
    assert snapshot.status_flags == {"OB", "LB"}
    assert snapshot.battery_charge == 14.0
    assert snapshot.runtime_seconds == 125.0
    assert snapshot.load_percent == 53.0
