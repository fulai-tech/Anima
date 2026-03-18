from __future__ import annotations

from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from core.models import DeviceCommand


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

    return app
