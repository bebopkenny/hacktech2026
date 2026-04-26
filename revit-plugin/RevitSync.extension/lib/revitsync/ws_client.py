"""
Singleton WebSocket client built on .NET's System.Net.WebSockets.ClientWebSocket.

We use the .NET implementation (rather than pip's websocket-client) so the
plugin runs cleanly under pyRevit's IronPython 3 engine without any pip
dependency.
"""
import json
import threading
import time

import clr
clr.AddReference("System")

from System import Uri, Array, Byte, ArraySegment
from System.Net.WebSockets import ClientWebSocket, WebSocketMessageType
from System.Text import Encoding
from System.Threading import CancellationToken

from revitsync.config import WS_URL, SESSION_ID
from revitsync import notifications


_client_instance = None
_lock = threading.Lock()

_RECV_BUFFER_SIZE = 8192
_RECONNECT_DELAY_S = 5


def get_ws_client():
    global _client_instance
    with _lock:
        if _client_instance is None:
            _client_instance = WSClient()
    return _client_instance


class WSClient:
    def __init__(self):
        self.connected = False
        self.last_error = None
        self._ws = None
        self._send_lock = threading.Lock()
        self._stop = False
        self._thread = threading.Thread(target=self._run_forever)
        self._thread.daemon = True
        self._thread.start()

    def send(self, payload):
        if not self.connected or self._ws is None:
            return
        try:
            with self._send_lock:
                data = Encoding.UTF8.GetBytes(payload)
                segment = ArraySegment[Byte](data)
                self._ws.SendAsync(segment, WebSocketMessageType.Text, True, CancellationToken.None).Wait()
        except Exception as e:
            self.last_error = "send: {}".format(e)
            self.connected = False

    def _connect(self):
        url = "{}/{}".format(WS_URL.rstrip("/"), SESSION_ID)
        self._ws = ClientWebSocket()
        try:
            self._ws.ConnectAsync(Uri(url), CancellationToken.None).Wait()
            self.connected = True
            self.last_error = None
            return True
        except Exception as e:
            self.last_error = "connect: {}".format(e)
            self.connected = False
            return False

    def _receive_loop(self):
        accumulated = bytearray()
        while not self._stop:
            try:
                buffer = Array.CreateInstance(Byte, _RECV_BUFFER_SIZE)
                segment = ArraySegment[Byte](buffer)
                result = self._ws.ReceiveAsync(segment, CancellationToken.None).Result

                if result.MessageType == WebSocketMessageType.Close:
                    self.connected = False
                    return

                for i in range(result.Count):
                    accumulated.append(buffer[i])

                if result.EndOfMessage:
                    text = bytes(accumulated).decode("utf-8")
                    accumulated = bytearray()
                    try:
                        conflict = json.loads(text)
                        notifications.show(conflict)
                    except Exception as e:
                        self.last_error = "bad message: {}".format(e)
            except Exception as e:
                self.last_error = "recv: {}".format(e)
                self.connected = False
                return

    def _run_forever(self):
        while not self._stop:
            if self._connect():
                self._receive_loop()
            if self._stop:
                return
            time.sleep(_RECONNECT_DELAY_S)
