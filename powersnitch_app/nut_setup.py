from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


NUT_CONF = Path("/etc/nut/nut.conf")
UPS_CONF = Path("/etc/nut/ups.conf")


@dataclass(slots=True)
class UsbUpsDevice:
    vendor_id: str
    model_id: str
    vendor: str
    model: str
    serial: str


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def _udev_properties(devnode: Path) -> dict[str, str]:
    result = _run(["udevadm", "info", "-q", "property", "-n", str(devnode)])
    if result.returncode != 0:
        return {}
    props: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        props[key.strip()] = value.strip()
    return props


def discover_usb_ups_devices() -> list[UsbUpsDevice]:
    devices: list[UsbUpsDevice] = []
    for devnode in sorted(Path("/dev/bus/usb").glob("*/*")):
        props = _udev_properties(devnode)
        vendor_id = props.get("ID_VENDOR_ID", "")
        model_id = props.get("ID_MODEL_ID", "")
        if not vendor_id or not model_id:
            continue
        if not _looks_like_supported_usb_ups(vendor_id, model_id):
            continue
        serial = props.get("ID_SERIAL_SHORT") or props.get("ID_SERIAL", "")
        vendor = props.get("ID_VENDOR", "UPS")
        model = props.get("ID_MODEL", "USB UPS")
        devices.append(
            UsbUpsDevice(
                vendor_id=vendor_id,
                model_id=model_id,
                vendor=vendor,
                model=model,
                serial=serial or f"{vendor_id}-{model_id}",
            )
        )
    deduped: dict[tuple[str, str, str], UsbUpsDevice] = {}
    for device in devices:
        deduped[(device.vendor_id, device.model_id, device.serial)] = device
    return list(deduped.values())


def _looks_like_supported_usb_ups(vendor_id: str, model_id: str) -> bool:
    supported = (
        vendor_id == "0764" and model_id == "0601",
        vendor_id == "051d",
        vendor_id == "09ae",
        vendor_id == "0665",
    )
    return any(supported)


def render_ups_conf(devices: list[UsbUpsDevice]) -> str:
    stanzas: list[str] = []
    for idx, device in enumerate(devices, start=1):
        stanzas.append(
            "\n".join(
                [
                    f"[ups{idx}]",
                    "    driver = usbhid-ups",
                    "    port = auto",
                    f"    vendorid = {device.vendor_id}",
                    f"    productid = {device.model_id}",
                    f"    serial = {device.serial}",
                    f'    desc = "{device.vendor} {device.model}"',
                ]
            )
        )
    if stanzas:
        return "\n\n".join(stanzas) + "\n"
    return (
        "[ups1]\n"
        "    driver = usbhid-ups\n"
        "    port = auto\n"
        '    desc = "Auto-configured USB UPS"\n'
    )


def current_nut_is_compatible() -> bool:
    if not NUT_CONF.exists() or not UPS_CONF.exists():
        return False
    nut_text = NUT_CONF.read_text(encoding="utf-8", errors="ignore")
    ups_text = UPS_CONF.read_text(encoding="utf-8", errors="ignore")
    if "MODE=standalone" not in nut_text:
        return False
    if "[" not in ups_text:
        return False
    result = _run(["upsc", "-l"])
    return result.returncode == 0 and bool(result.stdout.strip())


def backup_file(path: Path, backup_dir: Path) -> None:
    if not path.exists():
        return
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    shutil.copy2(path, backup_dir / f"{path.name}.{stamp}.bak")


def apply_configuration(backup_dir: Path) -> int:
    devices = discover_usb_ups_devices()
    backup_file(NUT_CONF, backup_dir)
    backup_file(UPS_CONF, backup_dir)
    NUT_CONF.write_text("MODE=standalone\n", encoding="utf-8")
    UPS_CONF.write_text(render_ups_conf(devices), encoding="utf-8")

    if shutil.which("systemctl"):
        _run(["systemctl", "restart", "nut-driver"])
        _run(["systemctl", "restart", "nut-server"])
    else:
        _run(["upsdrvctl", "start"])

    verification = _run(["upsc", "-l"])
    sys.stdout.write(verification.stdout)
    return verification.returncode


def print_summary() -> int:
    devices = discover_usb_ups_devices()
    if not devices:
        print("No supported USB UPS devices were detected.")
        return 1
    for idx, device in enumerate(devices, start=1):
        print(
            f"ups{idx}: vendor={device.vendor} model={device.model} "
            f"vendorid={device.vendor_id} productid={device.model_id} serial={device.serial}"
        )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover and configure local NUT USB UPS devices.")
    parser.add_argument("--print-config", action="store_true", help="Print generated ups.conf content and exit.")
    parser.add_argument("--apply", action="store_true", help="Write /etc/nut/nut.conf and /etc/nut/ups.conf.")
    parser.add_argument(
        "--backup-dir",
        default="/opt/powersnitch/data/nut-backups",
        help="Directory used for NUT config backups when applying changes.",
    )
    parser.add_argument("--check-compatible", action="store_true", help="Exit 0 if current NUT config is compatible.")
    args = parser.parse_args()

    if args.check_compatible:
        raise SystemExit(0 if current_nut_is_compatible() else 1)
    if args.print_config:
        sys.stdout.write(render_ups_conf(discover_usb_ups_devices()))
        return
    if args.apply:
        raise SystemExit(apply_configuration(Path(args.backup_dir)))
    raise SystemExit(print_summary())


if __name__ == "__main__":
    main()
