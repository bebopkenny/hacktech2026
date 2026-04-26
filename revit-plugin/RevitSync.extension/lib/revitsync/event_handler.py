"""DocumentChanged listener. Keep work here minimal — it runs on the Revit UI thread."""
import threading

from revitsync.serializer import serialize_change_event
from revitsync.ws_client import get_ws_client


class RevitChangeHandler:
    def __init__(self, uiapp):
        self.uiapp = uiapp
        self.ws = get_ws_client()

    def on_document_changed(self, sender, args):
        added    = [eid.IntegerValue for eid in args.GetAddedElementIds()]
        modified = [eid.IntegerValue for eid in args.GetModifiedElementIds()]
        deleted  = [eid.IntegerValue for eid in args.GetDeletedElementIds()]

        if not (added or modified or deleted):
            return

        doc = args.GetDocument()
        payload = serialize_change_event(doc, added, modified, deleted)

        threading.Thread(target=self.ws.send, args=(payload,), daemon=True).start()
