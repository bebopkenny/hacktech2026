# revit-plugin

Runs inside Revit via pyRevit. Listens for model changes, ships them to the
coordination service over WebSocket, and surfaces inbound conflict alerts as
non-blocking WPF toast notifications in the corner of the screen.

## Layout

```
revit-plugin/
  RevitSync.extension/                  pyRevit extension root
    startup.py                          auto-runs on pyRevit load — registers DocumentChanged
    lib/revitsync/                      shared library (added to sys.path by pyRevit)
      config.py                         env-driven WS_URL / SESSION_ID
      serializer.py                     Revit elements -> wire JSON
      event_handler.py                  DocumentChanged -> serializer -> ws_client
      ws_client.py                      persistent WS, auto-reconnect, dispatches to notifications
      notifications.py                  WPF toast UI on a dedicated STA dispatcher thread
    RevitSync.tab/Sync.panel/           ribbon UI
      Status.pushbutton/                shows connection state + config
      Test.pushbutton/                  fires a fake conflict to verify the toast UI
  install.ps1                           Windows installer (run once per machine)
  test_harness.py                       end-to-end test from a non-Revit Python (uses websockets)
```

## Requirements

- Windows + Revit
- [pyRevit](https://github.com/eirannejad/pyRevit) installed
- pyRevit's **CPython 3** engine selected (not IronPython)
  Switch via the pyRevit ribbon: `pyRevit -> Settings -> Engines`.

## Install

From a PowerShell prompt:

```powershell
cd revit-plugin
.\install.ps1
```

The installer:
1. Copies `RevitSync.extension/` into your pyRevit extensions directory.
2. Installs `websocket-client` into pyRevit's CPython 3.
3. Prompts for the WebSocket URL and your session ID, saves them as user env vars.
4. Tells you to reload pyRevit.

After install, open Revit. A new **RevitSync** tab should appear with two buttons:

- **Status** — confirms the plugin is connected to the server.
- **Test Toast** — fires a sample notification so you can verify the UI without touching the server.

## Environment variables

| Var | Default | Purpose |
|---|---|---|
| `REVITSYNC_WS_URL` | `ws://107.191.50.160:8000/ws` | Coordination service base URL (no trailing session id) |
| `REVITSYNC_SESSION_ID` | `user-1` | Unique per person — appended to the WS URL |
| `REVITSYNC_TOAST_LIFETIME_S` | `8` | Seconds a toast stays on screen |

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

Canonical schema: `coordination-service/models.py` (`ChangeEvent`).

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

Canonical schema: `coordination-service/models.py` (`EnrichedConflict`).

## Threading model

- `DocumentChanged` runs on the Revit UI thread — handler does the bare minimum and pushes work onto a daemon thread.
- `ws_client` runs `run_forever` on its own thread; receive callbacks fire there.
- `notifications` spins up a dedicated STA thread with a WPF `Dispatcher`. Toasts are scheduled onto it via `BeginInvoke`, so the WS thread never touches WPF directly and Revit's UI thread is never blocked.

## Test without Revit

```bash
pip install websockets
python revit-plugin/test_harness.py ws://107.191.50.160:8000/ws
```

Replays a wall/door conflict scenario against a real coordination service and prints the enriched conflict that comes back.
