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
    "lumi.sensor": "sensor",
    "lumi.gateway": "gateway",
    "chuangmi.plug": "plug",
    "chuangmi.camera": "camera",
    "xiaomi.wifispeaker": "speaker",
    "xiaomi.repeater": "repeater",
}


class MIoTAdapter(BaseAdapter):
    name = "miot"

    def __init__(self, settings_store=None) -> None:
        self._known_devices: dict[str, miio.Device] = {}
        self._device_infos: dict[str, dict] = {}
        self._settings = settings_store
        self._cloud_logged_in = False

    def _guess_device_type(self, model: str) -> str:
        for prefix, dtype in MODEL_TYPE_MAP.items():
            if model.startswith(prefix):
                return dtype
        return "unknown"

    def _build_device_id(self, ip: str, model: str) -> str:
        safe_ip = ip.replace(".", "_")
        safe_model = model.replace(".", "_")
        return f"miot_{safe_ip}_{safe_model}"

    def _build_device_id_from_did(self, did: str) -> str:
        return f"miot_cloud_{did}"

    # ── Cloud Discovery (primary) ──

    async def _discover_cloud(self) -> list[Device]:
        """Discover devices via Xiaomi Cloud API — most reliable method."""
        if not self._settings:
            return []

        creds = self._settings.get_xiaomi_credentials()
        if not creds:
            logger.debug("No Xiaomi Cloud credentials configured, skipping cloud discovery")
            return []

        username, password = creds
        country = self._settings.get_xiaomi_country()
        devices: list[Device] = []

        try:
            from micloud import MiCloud
            mc = MiCloud(username=username, password=password)
            mc.login()
            self._cloud_logged_in = True

            cloud_devices = mc.get_devices(country=country) or []
            logger.info("Xiaomi Cloud returned %d devices (country=%s)", len(cloud_devices), country)

            for cd in cloud_devices:
                try:
                    did = str(cd.get("did", ""))
                    ip = cd.get("localip", "")
                    token = cd.get("token", "")
                    model = cd.get("model", "unknown")
                    name = cd.get("name", model)
                    is_online = cd.get("isOnline", False)

                    if not did:
                        continue

                    device_id = self._build_device_id_from_did(did)
                    device_type = self._guess_device_type(model)

                    device = Device(
                        device_id=device_id,
                        name=name,
                        adapter=self.name,
                        type=device_type,
                        online=bool(is_online),
                        capabilities=self._default_capabilities(device_type),
                        sensors=self._default_sensors(device_type),
                    )
                    devices.append(device)

                    if ip and token and token != "0" * 32:
                        self._device_infos[device_id] = {
                            "ip": ip, "token": token, "model": model, "did": did,
                        }

                except Exception:
                    logger.exception("Failed to process cloud device: %s", cd.get("did", "?"))

        except Exception as e:
            self._cloud_logged_in = False
            logger.exception("Xiaomi Cloud discovery failed: %s", e)

        return devices

    # ── Local Network Discovery (UDP broadcast) ──

    async def _discover_local(self) -> list[Device]:
        """Discover Xiaomi devices via UDP broadcast handshake on port 54321.
        Finds all miio devices on the local network, even without tokens."""
        import socket
        import struct

        HELLO = bytes.fromhex(
            "21310020ffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        )
        PORT = 54321
        devices: list[Device] = []

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(3)

            sock.sendto(HELLO, ("<broadcast>", PORT))
            logger.info("Sent miio UDP broadcast on port %d...", PORT)

            while True:
                try:
                    data, addr = sock.recvfrom(1024)
                    ip = addr[0]

                    if len(data) < 32 or data[:2] != b"\x21\x31":
                        continue

                    did = struct.unpack(">I", data[8:12])[0]
                    token_bytes = data[16:32]
                    token = token_bytes.hex()
                    has_token = token != "0" * 32 and token != "f" * 32

                    device_id = f"miot_local_{did}"

                    # Try to get model if we have a token
                    model = "xiaomi.device"
                    device_type = "unknown"
                    if has_token:
                        try:
                            dev = miio.Device(ip=ip, token=token)
                            info = dev.info()
                            model = info.model or model
                            device_type = self._guess_device_type(model)
                        except Exception:
                            pass

                    name = f"小米设备 ({ip})" if not has_token else f"{model} ({ip})"

                    device = Device(
                        device_id=device_id,
                        name=name,
                        adapter=self.name,
                        type=device_type,
                        online=True,
                        capabilities=self._default_capabilities(device_type) if has_token else [],
                        sensors=self._default_sensors(device_type) if has_token else [],
                    )
                    devices.append(device)

                    if has_token:
                        self._device_infos[device_id] = {
                            "ip": ip, "token": token, "model": model, "did": str(did),
                        }
                    else:
                        # Store IP + DID so user can add token later
                        self._device_infos[device_id] = {
                            "ip": ip, "token": "", "model": model, "did": str(did),
                            "needs_token": True,
                        }

                    logger.info(
                        "Local scan: ip=%s did=%d token=%s",
                        ip, did, "available" if has_token else "needs_setup",
                    )

                except socket.timeout:
                    break

            sock.close()

        except Exception:
            logger.exception("UDP broadcast discovery failed")

        logger.info("Local scan found %d Xiaomi devices", len(devices))
        return devices

    async def _load_manual_devices(self) -> list[Device]:
        """Load manually added devices from settings store."""
        if not self._settings:
            return []

        manual = self._settings.get("manual_devices", [])
        devices: list[Device] = []

        for md in manual:
            ip = md.get("ip", "")
            token = md.get("token", "")
            model = md.get("model", "manual")
            name = md.get("name", f"{model} ({ip})")
            device_type = md.get("device_type", self._guess_device_type(model))

            device_id = self._build_device_id(ip, model)
            device = Device(
                device_id=device_id,
                name=name,
                adapter=self.name,
                type=device_type,
                online=True,
                capabilities=self._default_capabilities(device_type),
                sensors=self._default_sensors(device_type),
            )
            devices.append(device)
            self._device_infos[device_id] = {"ip": ip, "token": token, "model": model}

        if manual:
            logger.info("Loaded %d manual devices from config", len(manual))
        return devices

    async def discover(self) -> list[Device]:
        seen_ips: set[str] = set()
        devices: list[Device] = []

        # 1. Load manually added devices (always first, highest priority)
        manual = await self._load_manual_devices()
        for d in manual:
            info = self._device_infos.get(d.device_id, {})
            if info.get("ip"):
                seen_ips.add(info["ip"])
        devices.extend(manual)

        # 2. Try cloud discovery
        cloud = await self._discover_cloud()
        for d in cloud:
            info = self._device_infos.get(d.device_id, {})
            ip = info.get("ip", "")
            if ip and ip not in seen_ips:
                seen_ips.add(ip)
                devices.append(d)

        # 3. Local network UDP scan (finds devices even without tokens)
        local = await self._discover_local()
        for d in local:
            info = self._device_infos.get(d.device_id, {})
            ip = info.get("ip", "")
            if ip and ip not in seen_ips:
                seen_ips.add(ip)
                devices.append(d)

        logger.info("MIoT discovered %d devices total (%d manual, %d cloud, %d local)",
                     len(devices), len(manual), len(cloud), len(local))
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
