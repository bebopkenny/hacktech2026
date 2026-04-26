"""Singleton WebSocket client. Persistent connection, auto-reconnect, dispatches alerts to the toast UI."""
import json
import threading

import websocket  # pip install websocket-client (CPython 3 only)

from revitsync.config import WS_URL, SESSION_ID
from revitsync import notifications


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
        self.connected = False
        self.last_error = None
        self._thread = threading.Thread(target=self._run_forever, daemon=True)
        self._thread.start()

    def send(self, payload: str):
        if self._ws and self._ws.sock and self._ws.sock.connected:
            try:
                self._ws.send(payload)
            except Exception as e:
                self.last_error = str(e)

    def _on_open(self, ws):
        self.connected = True
        self.last_error = None

    def _on_close(self, ws, status_code, msg):
        self.connected = False

    def _on_message(self, ws, message: str):
        try:
            conflict = json.loads(message)
            notifications.show(conflict)
        except Exception as e:
            self.last_error = f"bad message: {e}"

    def _on_error(self, ws, error):
        self.last_error = str(error)

    def _run_forever(self):
        url = "{}/{}".format(WS_URL.rstrip("/"), SESSION_ID)
        self._ws = websocket.WebSocketApp(
            url,
            on_open=self._on_open,
            on_close=self._on_close,
            on_message=self._on_message,
            on_error=self._on_error,
        )
        self._ws.run_forever(reconnect=5)
