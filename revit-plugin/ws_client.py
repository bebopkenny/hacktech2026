"""
Singleton WebSocket client. Maintains one persistent connection to the coordination
service, auto-reconnects on drop, and dispatches incoming conflict alerts to the UI.
"""
import json
import threading
import websocket  # pip install websocket-client
from config import WS_URL, SESSION_ID
from conflict_display import show_conflict


_client_instance = None
_lock = threading.Lock()


def get_ws_client() -> "WSClient":
    global _client_instance
    with _lock:
        if _client_instance is None:
            _client_instance = WSClient()
    return _client_instance


class WSClient:
    def __init__(self):
        self._ws = None
        self._thread = threading.Thread(target=self._run_forever, daemon=True)
        self._thread.start()

    def send(self, payload: str):
        if self._ws and self._ws.sock and self._ws.sock.connected:
            self._ws.send(payload)

    def _on_message(self, ws, message: str):
        try:
            conflict = json.loads(message)
            # Dispatch back to Revit UI thread via ExternalEvent if needed.
            show_conflict(conflict)
        except Exception:
            pass

    def _on_error(self, ws, error):
        print(f"RevitSync WS error: {error}")

    def _run_forever(self):
        # websocket-client will reconnect automatically with reconnect=5 (seconds).
        self._ws = websocket.WebSocketApp(
            f"{WS_URL}/{SESSION_ID}",
            on_message=self._on_message,
            on_error=self._on_error,
        )
        self._ws.run_forever(reconnect=5)
