import os

# Update WS_URL to point at your deployed Vultr VM, or localhost for local dev.
WS_URL = os.getenv("REVITVYNC_WS_URL", "ws://107.191.50.160:8000/ws")

# Unique identifier for this Revit session / user. Set per machine.
SESSION_ID = os.getenv("REVITVYNC_SESSION_ID", "user-1")


from pyrevit import forms
from Autodesk.Revit.UI import TaskDialog

forms.alert("Hello World from pyRevit!", title="pyRevit Demo")
TaskDialog.Show("Hello World", "This is a Revit-native message.")