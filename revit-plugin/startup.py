"""
pyRevit entry point. pyRevit executes this file when the extension loads.
We register the DocumentChanged listener here so it survives the session.
"""
from pyrevit import script
from event_handler import RevitChangeHandler

logger = script.get_logger()

def register_handlers(uiapp):
    handler = RevitChangeHandler(uiapp)
    uiapp.Application.DocumentChanged += handler.on_document_changed
    logger.info("RevitSync: DocumentChanged handler registered")

# pyRevit calls __revit__ at load time; hook into its Application here.
try:
    register_handlers(__revit__)  # noqa: F821 — pyRevit injects __revit__ at runtime
except Exception as e:
    logger.error(f"RevitSync startup failed: {e}")
