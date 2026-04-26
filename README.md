# RevitSync — Real-Time Collaborative BIM

Real-time collaboration extension for Autodesk Revit. Multiple engineers can work on the same model simultaneously; conflicts are detected automatically and explained in plain English by an AI layer.

## Architecture

```
┌─────────────────────┐        WebSocket        ┌──────────────────────────┐
│   Revit Instance A  │ ──── change events ────▶ │                          │
│   (pyRevit plugin)  │                           │   Coordination Service   │
│                     │ ◀─── conflict alerts ──── │   (FastAPI + WS hub)     │
└─────────────────────┘                           │                          │
                                                  │  dependency graph +      │
┌─────────────────────┐        WebSocket          │  conflict detector       │
│   Revit Instance B  │ ──── change events ────▶ │                          │
│   (pyRevit plugin)  │                           └────────────┬─────────────┘
│                     │ ◀─── conflict alerts ────              │
└─────────────────────┘                                        │ conflict objects
                                                               ▼
                                                  ┌──────────────────────────┐
                                                  │       AI Layer           │
                                                  │  (Gemma 4 / K2-Think-V2) │
                                                  │  structured → plain      │
                                                  │  English warnings        │
                                                  └──────────────────────────┘
```

## Team Ownership

| Directory | Owner | Needs Revit? |
|---|---|---|
| `revit-plugin/` | Person 1 | Yes (Windows + Revit) |
| `coordination-service/` | Person 2 | No — pure Python |
| `ui/` | Person 3 | Yes for panel; No for ThreeJS demo |
| `ai-layer/` | Person 4 | No — pure Python |

## Quick Start (local dev)

```bash
# Start coordination service + AI layer together
docker-compose up

# Or run coordination service alone
cd coordination-service && uvicorn main:app --reload --port 8000

# Run AI layer
cd ai-layer && uvicorn main:app --reload --port 8001
```

## Event Flow

1. A user modifies an element in Revit (wall moved, door added, etc.)
2. `revit-plugin` serializes the `DocumentChanged` event to JSON and sends it over WebSocket
3. `coordination-service` receives it, updates the dependency graph, and runs conflict detection
4. If a conflict is found, the raw conflict object is sent to the `ai-layer`
5. `ai-layer` returns a plain-English warning + resolution suggestion
6. The enriched conflict is broadcast back to all connected Revit instances
7. Each instance's UI panel displays the notification

## Wire Format

See `coordination-service/models.py` for the canonical Pydantic models shared across all services.

## Deployment

The coordination service and AI layer both run on a Vultr VM via `docker-compose`.

### Fresh VM (one-shot bootstrap)

On a clean Ubuntu Vultr VM, as root:

```bash
curl -fsSL https://raw.githubusercontent.com/bebopkenny/hacktech2026/testing/deploy/bootstrap.sh | bash
```

This installs Docker, clones the repo to `/opt/revitsync`, prompts for `K2_API_KEY`, opens UFW ports 8000/8001, and brings the stack up. At the end it prints the `ws://<ip>:8000/ws` URL the Revit plugin should point at.

To skip the interactive prompt, set `K2_API_KEY` first:

```bash
K2_API_KEY=sk-... bash <(curl -fsSL https://raw.githubusercontent.com/bebopkenny/hacktech2026/testing/deploy/bootstrap.sh)
```

### Update an existing VM

```bash
cd /opt/revitsync
sudo bash deploy/update.sh
```

Pulls the latest commit on the configured branch and runs `docker compose up -d --build`.

### Plugin install (Windows + Revit)

See [revit-plugin/README.md](revit-plugin/README.md). TL;DR: install pyRevit, run `revit-plugin\install.ps1`, reload pyRevit.
