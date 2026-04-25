"""
pyRevit dockable panel for RevitSync conflict notifications.
Shows a live-updating list of conflicts without blocking Revit.
"""
import json
import threading
import clr  # noqa: IronPython / pyRevit

clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")

from System.Windows import Application, Window  # noqa
from System.Windows.Threading import Dispatcher  # noqa
import websocket  # pip install websocket-client (available inside pyRevit env)

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

WS_URL = os.getenv("REVITVYNC_WS_URL", "ws://localhost:8000/ws")
SESSION_ID = os.getenv("REVITVYNC_SESSION_ID", "panel-observer")


class ConflictPanel:
    def __init__(self):
        self.window = None
        self.listbox = None
        self._start_ws()

    def show(self):
        # Load XAML — pyRevit provides WPFWindow helper.
        from pyrevit import forms
        self.window = forms.WPFWindow("panel.xaml")
        self.listbox = self.window.FindName("ConflictList")
        self.window.Show()

    def _start_ws(self):
        t = threading.Thread(target=self._run_ws, daemon=True)
        t.start()

    def _run_ws(self):
        ws = websocket.WebSocketApp(
            f"{WS_URL}/{SESSION_ID}",
            on_message=self._on_message,
        )
        ws.run_forever(reconnect=5)

    def _on_message(self, ws, message):
        try:
            conflict = json.loads(message)
            text = conflict.get("plain_english", "Conflict detected")
            # Marshal UI update to WPF dispatcher.
            if self.listbox:
                self.listbox.Dispatcher.Invoke(lambda: self.listbox.Items.Add(text))
        except Exception:
            pass


panel = ConflictPanel()
panel.show()
