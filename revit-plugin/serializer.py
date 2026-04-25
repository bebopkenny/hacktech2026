"""
Converts raw Revit element IDs into the JSON payload the coordination service expects.
Only pull the fields the conflict detector actually needs — minimize API calls here.
"""
import json
from datetime import datetime, timezone
from config import SESSION_ID

from Autodesk.Revit.DB import ElementId, BuiltInParameter  # noqa: Revit API


def _element_snapshot(doc, element_id: int) -> dict:
    """Return a minimal dict describing a single element."""
    eid = ElementId(element_id)
    elem = doc.GetElement(eid)
    if elem is None:
        return {"element_id": element_id}

    snapshot = {
        "element_id": element_id,
        "category": elem.Category.Name if elem.Category else "Unknown",
    }

    # Level association — useful for spatial conflict detection.
    level_param = elem.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM)
    if level_param and level_param.AsElementId() != ElementId.InvalidElementId:
        level_elem = doc.GetElement(level_param.AsElementId())
        snapshot["level"] = level_elem.Name if level_elem else None

    # Host element (e.g. the wall a door lives on).
    if hasattr(elem, "Host") and elem.Host is not None:
        snapshot["host_id"] = elem.Host.Id.IntegerValue

    return snapshot


def serialize_change_event(doc, added: list, modified: list, deleted: list) -> str:
    payload = {
        "session_id": SESSION_ID,
        "document": doc.Title,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "added":    [_element_snapshot(doc, eid) for eid in added],
        "modified": [_element_snapshot(doc, eid) for eid in modified],
        "deleted":  deleted,  # deleted IDs have no live element to query
    }
    return json.dumps(payload)
