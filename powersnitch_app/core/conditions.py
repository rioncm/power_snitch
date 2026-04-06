from __future__ import annotations

from powersnitch_app.models import ConditionResult, DeviceSnapshot, STATUS_FLAGS


def evaluate_conditions(
    snapshot: DeviceSnapshot,
    battery_low_pct_threshold: float,
    runtime_low_threshold_seconds: float,
) -> list[ConditionResult]:
    results: list[ConditionResult] = []
    for key, flag in STATUS_FLAGS.items():
        results.append(
            ConditionResult(
                key=key,
                active=flag in snapshot.status_flags,
                value=flag if flag in snapshot.status_flags else None,
                reason=f"UPS status contains {flag}" if flag in snapshot.status_flags else f"{flag} not present",
            )
        )
    results.append(
        ConditionResult(
            key="battery_low_pct",
            active=snapshot.battery_charge is not None and snapshot.battery_charge < battery_low_pct_threshold,
            value=snapshot.battery_charge,
            reason=f"Battery below {battery_low_pct_threshold}%",
        )
    )
    results.append(
        ConditionResult(
            key="runtime_low",
            active=snapshot.runtime_seconds is not None and snapshot.runtime_seconds < runtime_low_threshold_seconds,
            value=snapshot.runtime_seconds,
            reason=f"Runtime below {runtime_low_threshold_seconds} seconds",
        )
    )
    results.append(
        ConditionResult(
            key="ups_communication_lost",
            active=not snapshot.is_reachable,
            value=None,
            reason="UPS polling failed" if not snapshot.is_reachable else "UPS reachable",
        )
    )
    results.append(
        ConditionResult(
            key="unknown_state",
            active=not snapshot.status_flags,
            value=None,
            reason="No UPS status flags reported" if not snapshot.status_flags else "UPS flags reported",
        )
    )
    return results


def build_alert_text(
    ups_name: str,
    condition_key: str,
    condition_state: str,
    snapshot: DeviceSnapshot,
    extra_text: str = "",
) -> tuple[str, str]:
    title_state = "Recovered" if condition_state == "recovered" else "Active"
    subject = f"{ups_name}: {condition_key.replace('_', ' ')} {title_state.lower()}"
    lines = [
        f"UPS: {ups_name}",
        f"Condition: {condition_key}",
        f"State: {condition_state}",
        f"Time: {snapshot.observed_at.isoformat()}",
        f"Status Flags: {', '.join(sorted(snapshot.status_flags)) or 'none'}",
        f"Battery Charge: {snapshot.battery_charge if snapshot.battery_charge is not None else 'n/a'}",
        f"Runtime Seconds: {snapshot.runtime_seconds if snapshot.runtime_seconds is not None else 'n/a'}",
        f"Input Voltage: {snapshot.input_voltage if snapshot.input_voltage is not None else 'n/a'}",
        f"Load Percent: {snapshot.load_percent if snapshot.load_percent is not None else 'n/a'}",
    ]
    if extra_text.strip():
        lines.extend(["", extra_text.strip()])
    return subject, "\n".join(lines)

