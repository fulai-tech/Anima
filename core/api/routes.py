from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.models import DeviceCommand

logger = logging.getLogger(__name__)


class XiaomiLoginRequest(BaseModel):
    username: str
    password: str
    country: str = "cn"


class LLMConfigRequest(BaseModel):
    api_key: str
    model: str = "gpt-4o"
    base_url: str = ""
    disable_thinking: bool = False


def create_app(app_state: dict[str, Any]) -> FastAPI:
    app = FastAPI(title="Anima", description="Make Every Hardware Intelligent", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    @app.get("/api/devices")
    async def list_devices():
        discovery = app_state["discovery"]
        return [d.model_dump() for d in discovery.get_all_devices()]

    @app.get("/api/devices/{device_id}")
    async def get_device(device_id: str):
        discovery = app_state["discovery"]
        device = discovery.get_device(device_id)
        if not device:
            return {"error": "Device not found"}, 404
        return device.model_dump()

    @app.post("/api/devices/{device_id}/command")
    async def send_command(device_id: str, command: DeviceCommand):
        discovery = app_state["discovery"]
        result = await discovery.execute_command(
            device_id, command.action, command.params,
        )
        return result.model_dump()

    @app.get("/api/rooms")
    async def list_rooms():
        return app_state.get("rooms", [])

    @app.post("/api/chat")
    async def chat(body: dict):
        message = body.get("message", "")
        # Simple chat: pass user message as a command event
        # Full chat implementation in v0.2
        return {"reply": f"Received: {message}", "status": "chat coming in v0.2"}

    @app.get("/api/decisions")
    async def list_decisions():
        memory = app_state["memory"]
        history = await memory.get_history("default", limit=50)
        return history

    @app.post("/api/scan")
    async def trigger_scan():
        discovery = app_state["discovery"]
        new_devices = await discovery.scan()
        return {"new_devices": len(new_devices), "total": len(discovery.devices)}

    # ── Settings API ──

    @app.get("/api/settings")
    async def get_settings():
        store = app_state["settings"]
        data = store.get_all()
        # Mask sensitive fields
        safe = dict(data)
        if "xiaomi_cloud_pass" in safe:
            safe["xiaomi_cloud_pass"] = "***"
        if "llm_api_key" in safe:
            safe["llm_api_key"] = safe["llm_api_key"][:8] + "***"
        return safe

    @app.get("/api/settings/xiaomi/status")
    async def xiaomi_status():
        store = app_state["settings"]
        return {
            "configured": store.is_xiaomi_configured(),
            "username": store.get("xiaomi_cloud_user", ""),
            "country": store.get_xiaomi_country(),
        }

    @app.post("/api/settings/xiaomi/connect")
    async def xiaomi_connect(req: XiaomiLoginRequest):
        store = app_state["settings"]
        # Test login before saving
        try:
            from micloud import MiCloud
            mc = MiCloud(username=req.username, password=req.password)
            mc.login()
            device_count = len(mc.get_devices(country=req.country) or [])
        except Exception as e:
            logger.exception("Xiaomi Cloud login failed")
            return {"success": False, "error": f"登录失败: {e}"}

        # Save credentials
        store.update({
            "xiaomi_cloud_user": req.username,
            "xiaomi_cloud_pass": req.password,
            "xiaomi_cloud_country": req.country,
        })

        # Trigger re-scan
        discovery = app_state["discovery"]
        new_devices = await discovery.scan()

        return {
            "success": True,
            "cloud_devices": device_count,
            "discovered": len(new_devices),
            "total": len(discovery.devices),
        }

    @app.post("/api/settings/xiaomi/disconnect")
    async def xiaomi_disconnect():
        store = app_state["settings"]
        store.delete("xiaomi_cloud_user")
        store.delete("xiaomi_cloud_pass")
        store.delete("xiaomi_cloud_country")
        return {"success": True}

    @app.get("/api/settings/llm/status")
    async def llm_status():
        from core.config import settings as env_settings
        store = app_state["settings"]
        api_key = store.get("llm_api_key", "") or env_settings.llm_api_key
        return {
            "configured": bool(api_key),
            "model": store.get("llm_model", "") or env_settings.llm_model,
            "base_url": store.get("llm_base_url", "") or env_settings.llm_base_url or "",
            "source": "dashboard" if store.get("llm_api_key") else "env",
        }

    @app.post("/api/settings/llm/configure")
    async def llm_configure(req: LLMConfigRequest):
        store = app_state["settings"]
        store.update({
            "llm_api_key": req.api_key,
            "llm_model": req.model,
            "llm_base_url": req.base_url,
            "llm_disable_thinking": req.disable_thinking,
        })
        return {"success": True, "model": req.model}

    return app
