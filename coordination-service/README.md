# coordination-service — Person 2

Pure Python. No Revit required. Receives change events from all connected Revit sessions, maintains a dependency graph, detects conflicts, and broadcasts enriched alerts back.

## Files

| File | Purpose |
|---|---|
| `main.py` | FastAPI app — HTTP health endpoint + WebSocket route |
| `ws_hub.py` | Connection manager: tracks sessions, broadcasts to all but sender |
| `models.py` | Pydantic schemas — single source of truth for the wire format |
| `dependency_graph.py` | Tracks which elements depend on which (host→hosted, shared levels, etc.) |
| `conflict_detector.py` | Inspects incoming events against current graph state; emits conflict objects |
| `ai_client.py` | HTTP client that posts raw conflict objects to the AI layer and awaits enriched text |
| `sample_data/` | JSON fixtures to exercise the full pipeline without a live Revit instance |

## Running locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Test with the sample event sender:
```bash
python sample_data/send_sample.py
```

## WebSocket protocol

**Client → Server** (change event):
```json
{
  "session_id": "user-1",
  "document": "hospital.rvt",
  "timestamp": "2026-04-25T10:00:00Z",
  "added":    [{ "element_id": 1, "category": "Walls", "level": "L1" }],
  "modified": [{ "element_id": 2, "category": "Doors", "host_id": 1, "level": "L1" }],
  "deleted":  [3]
}
```

**Server → Client** (conflict alert, broadcast to all sessions):
```json
{
  "conflict_id": "cf-001",
  "severity": "error",
  "elements": [1, 2],
  "raw_reason": "host_modified_while_child_owned_by_other_session",
  "plain_english": "...",
  "suggestion": "..."
}
```

`plain_english` and `suggestion` are filled in by the AI layer; the service sends the raw conflict immediately and optionally re-broadcasts the enriched version when AI responds.

## Conflict types detected

- **Host/child violation** — a wall is moved/deleted while another session owns a door hosted on it
- **Level deletion** — a level is deleted while elements on it are owned by another session
- **Geometry overlap** — two sessions place structural elements in the same bounding region (Phase 2)

## Deployment (Vultr VM)

See `deploy/` for Dockerfile and `setup.sh`. The service expects these env vars:

```
AI_LAYER_URL=http://localhost:8001   # or the AI layer's internal address
PORT=8000
```
