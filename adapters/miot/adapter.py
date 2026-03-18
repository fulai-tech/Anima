from __future__ import annotations

import logging
from typing import Any

import miio

from adapters.base import BaseAdapter
from core.models import Device, Capability, Sensor, ActionResult

logger = logging.getLogger(__name__)

# Model prefix → device type mapping
MODEL_TYPE_MAP = {
    "zhimi.humidifier": "humidifier",
    "deerma.humidifier": "humidifier",
    "zhimi.airpurifier": "air_purifier",
    "xiaomi.aircondition": "air_conditioner",
    "midea.aircondition": "air_conditioner",
    "yeelink.light": "light",
    "xiaomi.light": "light",
    "philips.light": "light",
    "dreame.vacuum": "vacuum",
    "roborock.vacuum": "vacuum",
    "lumi.curtain": "curtain",
}


class MIoTAdapter(BaseAdapter):
    name = "miot"

    def __init__(self) -> None:
        self._known_devices: dict[str, miio.Device] = {}  # device_id → miio device object
        self._device_infos: dict[str, dict] = {}  # device_id → {ip, token, model}

    def _guess_device_type(self, model: str) -> str:
        for prefix, dtype in MODEL_TYPE_MAP.items():
            if model.startswith(prefix):
                return dtype
        return "unknown"

    def _build_device_id(self, ip: str, model: str) -> str:
        safe_ip = ip.replace(".", "_")
        safe_model = model.replace(".", "_")
        return f"miot_{safe_ip}_{safe_model}"

    async def discover(self) -> list[Device]:
        devices: list[Device] = []
        try:
            found = miio.Discovery.discover_mdns(timeout=5)
            for addr, info in found.items():
                try:
                    ip = info.ip if hasattr(info, "ip") else str(addr)
                    token = getattr(info, "token", None)
                    model = getattr(info, "model", "unknown")

                    if not token or token == "0" * 32:
                        logger.debug("Skipping device at %s — no token", ip)
                        continue

                    device_id = self._build_device_id(ip, model)
                    device_type = self._guess_device_type(model)

                    device = Device(
                        device_id=device_id,
                        name=f"{model} ({ip})",
                        adapter=self.name,
                        type=device_type,
                        capabilities=self._default_capabilities(device_type),
                        sensors=self._default_sensors(device_type),
                    )
                    devices.append(device)

                    # Cache miio device object for later control
                    self._device_infos[device_id] = {
                        "ip": ip, "token": token, "model": model,
                    }

                except Exception:
                    logger.exception("Failed to process discovered device at %s", addr)

        except Exception:
            logger.exception("MIoT mDNS discovery failed")

        logger.info("MIoT discovered %d devices", len(devices))
        return devices

    def _get_miio_device(self, device_id: str) -> miio.Device | None:
        if device_id in self._known_devices:
            return self._known_devices[device_id]

        info = self._device_infos.get(device_id)
        if not info:
            return None

        try:
            dev = miio.Device(ip=info["ip"], token=info["token"])
            self._known_devices[device_id] = dev
            return dev
        except Exception:
            logger.exception("Failed to create miio device for %s", device_id)
            return None

    async def subscribe(self, device: Device) -> None:
        # MIoT doesn't support push — we poll in the scheduler
        pass

    async def execute(self, device_id: str, action: str, params: dict[str, Any]) -> ActionResult:
        dev = self._get_miio_device(device_id)
        if not dev:
            return ActionResult(
                device_id=device_id, action=action, success=False,
                message=f"Device {device_id} not found or not reachable",
            )

        try:
            if action == "turn_on":
                dev.on()
            elif action == "turn_off":
                dev.off()
            elif action in ("set_humidity", "set_temperature", "set_brightness"):
                value = params.get("value")
                dev.send(f"set_{action.split('_')[-1]}", [value])
            elif action == "set_mode":
                mode = params.get("mode")
                dev.send("set_mode", [mode])
            elif action == "set_color_temp":
                kelvin = params.get("kelvin")
                dev.send("set_ct_abx", [kelvin, "smooth", 500])
            else:
                dev.send(action, list(params.values()) if params else [])

            logger.info("MIoT execute: %s.%s(%s) → OK", device_id, action, params)
            return ActionResult(device_id=device_id, action=action, success=True)

        except Exception as e:
            logger.exception("MIoT execute failed: %s.%s", device_id, action)
            return ActionResult(
                device_id=device_id, action=action, success=False, message=str(e),
            )

    def _default_capabilities(self, device_type: str) -> list[Capability]:
        common = [Capability(name="turn_on"), Capability(name="turn_off")]
        type_caps = {
            "humidifier": [
                Capability(name="set_humidity", params={"min": 30, "max": 80, "step": 10}),
                Capability(name="set_mode", params={"options": ["auto", "silent", "strong"]}),
            ],
            "air_conditioner": [
                Capability(name="set_temperature", params={"min": 16, "max": 30, "step": 1}),
                Capability(name="set_mode", params={"options": ["cool", "heat", "auto", "fan"]}),
            ],
            "light": [
                Capability(name="set_brightness", params={"min": 1, "max": 100, "step": 1}),
                Capability(name="set_color_temp", params={"min": 2700, "max": 6500}),
            ],
        }
        return common + type_caps.get(device_type, [])

    def _default_sensors(self, device_type: str) -> list[Sensor]:
        type_sensors = {
            "humidifier": [
                Sensor(name="humidity", unit="%"),
                Sensor(name="water_level", unit="%"),
            ],
            "air_conditioner": [
                Sensor(name="temperature", unit="°C"),
            ],
            "light": [
                Sensor(name="brightness", unit="%"),
                Sensor(name="color_temp", unit="K"),
            ],
        }
        return [Sensor(name="power", unit="on/off")] + type_sensors.get(device_type, [])
