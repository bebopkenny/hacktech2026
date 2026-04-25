"""
Manages all active WebSocket connections.
One connection per Revit session (session_id is the key).
"""
import json
from fastapi import WebSocket


class ConnectionHub:
    def __init__(self):
        # session_id → WebSocket
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, ws: WebSocket):
        await ws.accept()
        self._connections[session_id] = ws

    def disconnect(self, session_id: str):
        self._connections.pop(session_id, None)

    async def broadcast(self, payload: dict, exclude_session: str | None = None):
        """Send payload to every connected session except the sender."""
        message = json.dumps(payload)
        dead = []
        for sid, ws in self._connections.items():
            if sid == exclude_session:
                continue
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(sid)
        for sid in dead:
            self.disconnect(sid)

    async def send_to(self, session_id: str, payload: dict):
        ws = self._connections.get(session_id)
        if ws:
            await ws.send_text(json.dumps(payload))

    @property
    def active_sessions(self) -> list[str]:
        return list(self._connections.keys())


# Module-level singleton shared across the FastAPI app.
hub = ConnectionHub()
