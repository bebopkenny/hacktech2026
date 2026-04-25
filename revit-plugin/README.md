# revit-plugin — Person 1

Runs inside Revit via pyRevit. Listens for model changes, serializes them, and sends them to the coordination service. Receives conflict alerts and surfaces them in Revit.

## Files

| File | Purpose |
|---|---|
| `startup.py` | pyRevit entry point — registers all Revit event hooks |
| `event_handler.py` | `DocumentChanged` handler, coerces raw Revit API types to dicts |
| `serializer.py` | Converts Revit element snapshots → JSON matching the wire format |
| `ws_client.py` | Async WebSocket client — sends events, receives conflict broadcasts |
| `conflict_display.py` | Renders conflict alerts as Revit task dialogs / status bar messages |
| `config.py` | Single place for the WebSocket URL and session user ID |

## Setup

1. Install pyRevit on your Windows machine.
2. Drop this folder into your pyRevit extensions directory.
3. Edit `config.py` to point at the coordination service URL.
4. Reload pyRevit.

## Key Revit API touchpoints

- `__revit__.Application.DocumentChanged` — fires after every transaction commit
- `IUpdater` — alternative if you need pre-transaction hooks (not used here yet)
- `FilteredElementCollector` — used in `serializer.py` to grab element geometry/parameters

## Wire format (outbound)

```json
{
  "session_id": "user-abc",
  "document": "hospital_floor3.rvt",
  "timestamp": "2026-04-25T10:30:00Z",
  "added":    [{ "element_id": 123, "category": "Walls", "level": "L1" }],
  "modified": [{ "element_id": 456, "category": "Doors", "level": "L1", "host_id": 123 }],
  "deleted":  [789]
}
```

See `coordination-service/models.py` for the canonical schema.

## Wire format (inbound — conflict alert)

```json
{
  "conflict_id": "cf-001",
  "severity": "error",
  "plain_english": "You moved Wall #123, but Person B's Door #456 is hosted on it.",
  "suggestion": "Coordinate with Person B before committing, or rehost the door.",
  "elements": [123, 456]
}
```
