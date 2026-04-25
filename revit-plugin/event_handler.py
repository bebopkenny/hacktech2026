"""
Listens to Revit's DocumentChanged event and hands off to the WebSocket client.
DocumentChanged fires after every committed transaction — do as little work here
as possible to avoid blocking the Revit UI thread.
"""
import threading
from serializer import serialize_change_event
from ws_client import get_ws_client


class RevitChangeHandler:
    def __init__(self, uiapp):
        self.uiapp = uiapp
        self.ws = get_ws_client()

    def on_document_changed(self, sender, args):
        # args is a DocumentChangedEventArgs; extract element ID sets immediately
        # because they are only valid during this callback.
        added    = [eid.IntegerValue for eid in args.GetAddedElementIds()]
        modified = [eid.IntegerValue for eid in args.GetModifiedElementIds()]
        deleted  = [eid.IntegerValue for eid in args.GetDeletedElementIds()]

        if not (added or modified or deleted):
            return

        doc = args.GetDocument()
        payload = serialize_change_event(doc, added, modified, deleted)

        # Send on a background thread so we never stall the Revit UI.
        threading.Thread(target=self.ws.send, args=(payload,), daemon=True).start()
