# ui — Person 3

Two options — pick one or ship both:

**Option A** (`revit-panel/`) — a native pyRevit dockable panel. Runs on the second Windows machine alongside the pyRevit plugin. Receives conflict alerts via the same WebSocket the plugin uses and displays them in a persistent side panel instead of popup dialogs.

**Option B** (`threejs-demo/`) — a standalone browser page. Connects to the coordination service WebSocket and visualises a simple 3D scene. Conflict alerts animate in as overlays. No Revit needed — good for demos.

## Option A: revit-panel

### Files
| File | Purpose |
|---|---|
| `panel.py` | pyRevit panel script — WPF window backed by `panel.xaml` |
| `panel.xaml` | XAML layout for the dockable notification list |

### Setup
1. Copy the `revit-panel/` folder into your pyRevit extension.
2. Reload pyRevit — the "RevitSync" panel should appear in the ribbon.
3. The panel connects to the same WebSocket URL as the plugin (set in `config.py`).

### How it works
- Opens a `DockablePane` on startup.
- Spawns a background thread running a WebSocket listener.
- When a conflict arrives, it marshals to the WPF dispatcher and appends a row to the `ListView`.

## Option B: threejs-demo

### Files
| File | Purpose |
|---|---|
| `index.html` | Entry point — loads Three.js and the WS client |
| `ws_client.js` | Connects to the coordination service, dispatches conflict events |
| `renderer.js` | Three.js scene + conflict overlay rendering |

### Setup
```bash
# Just open in a browser — no build step.
open ui/threejs-demo/index.html
# Or serve it:
npx serve ui/threejs-demo
```
Point `WS_URL` in `ws_client.js` at the running coordination service.
