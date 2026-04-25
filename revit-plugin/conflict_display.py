"""
Surfaces conflict alerts inside the Revit UI.
Today: TaskDialog popup. Person 3 will replace/augment this with the panel UI.
"""
from Autodesk.Revit.UI import TaskDialog, TaskDialogIcon  # noqa: Revit API


def show_conflict(conflict: dict):
    """
    Called from the WS receive thread. Revit UI calls must happen on the main thread —
    if you hit a threading error here, wrap this in an IExternalEventHandler.
    """
    severity = conflict.get("severity", "warning")
    icon = TaskDialogIcon.TaskDialogIconWarning if severity == "warning" else TaskDialogIcon.TaskDialogIconError

    dlg = TaskDialog("RevitSync Conflict")
    dlg.MainIcon = icon
    dlg.MainInstruction = conflict.get("plain_english", "A conflict was detected.")
    dlg.MainContent = conflict.get("suggestion", "")
    dlg.Show()
