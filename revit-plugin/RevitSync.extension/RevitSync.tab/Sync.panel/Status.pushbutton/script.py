"""Show current RevitSync connection state."""
from pyrevit import forms

from revitsync.config import WS_URL, SESSION_ID
from revitsync.ws_client import get_ws_client

ws = get_ws_client()
state = "connected" if ws.connected else "disconnected"
last_err = ws.last_error or "(none)"

forms.alert(
    "Server : {}\n"
    "Session: {}\n"
    "State  : {}\n"
    "Last error: {}".format(WS_URL, SESSION_ID, state, last_err),
    title="RevitSync Status",
)
