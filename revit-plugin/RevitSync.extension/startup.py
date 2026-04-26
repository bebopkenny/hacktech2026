"""
pyRevit extension entry point.

pyRevit executes this file once when the extension is loaded into a Revit
session. We register the DocumentChanged listener and warm up the WebSocket
client here so they live for the rest of the session.
"""
from pyrevit import script

from revitsync.event_handler import RevitChangeHandler
from revitsync.ws_client import get_ws_client

logger = script.get_logger()

_handler = None


def register_handlers(uiapp):
    global _handler
    _handler = RevitChangeHandler(uiapp)
    uiapp.Application.DocumentChanged += _handler.on_document_changed
    get_ws_client()  # start the WS client thread now, not on first edit
    logger.info("RevitSync: DocumentChanged handler registered, WS client started")


try:
    register_handlers(__revit__)  # noqa: F821 -- pyRevit injects __revit__
except Exception as e:
    logger.error("RevitSync startup failed: {}".format(e))
