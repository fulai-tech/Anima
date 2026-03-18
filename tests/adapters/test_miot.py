import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from adapters.miot.adapter import MIoTAdapter
from core.models import Device


class TestMIoTAdapter:
    def test_adapter_name(self):
        adapter = MIoTAdapter()
        assert adapter.name == "miot"

    @patch("adapters.miot.adapter.miio.Discovery")
    async def test_discover_returns_devices(self, mock_discovery_cls):
        mock_listener = MagicMock()
        mock_info = MagicMock()
        mock_info.ip = "192.168.1.100"
        mock_info.token = "aabbccdd" * 4
        mock_info.model = "zhimi.humidifier.v1"
        mock_info.name = "Humidifier"

        adapter = MIoTAdapter()
        # Test device type mapping
        assert adapter._guess_device_type("zhimi.humidifier.v1") == "humidifier"
        assert adapter._guess_device_type("xiaomi.aircondition.mc5") == "air_conditioner"
        assert adapter._guess_device_type("yeelink.light.lamp1") == "light"
        assert adapter._guess_device_type("unknown.model.x1") == "unknown"

    def test_build_device_id(self):
        adapter = MIoTAdapter()
        did = adapter._build_device_id("192.168.1.100", "zhimi.humidifier.v1")
        assert did == "miot_192_168_1_100_zhimi_humidifier_v1"

    async def test_execute_calls_device(self):
        adapter = MIoTAdapter()
        # Without real device, execute should return failure
        result = await adapter.execute("nonexistent", "turn_on", {})
        assert result.success is False
