"""
FastAPI entry point.
  GET  /health          — liveness probe
  GET  /sessions        — list active WebSocket sessions
  WS   /ws/{session_id} — per-session WebSocket connection
"""
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from models import ChangeEvent
from ws_hub import hub
from dependency_graph import graph
from conflict_detector import detect_conflicts
from ai_client import enrich_conflict

app = FastAPI(title="RevitSync Coordination Service")


@app.get("/health")
def health():
    return {"status": "ok", "sessions": hub.active_sessions}


@app.get("/sessions")
def sessions():
    return {"active": hub.active_sessions}


@app.post("/inject")
async def inject(event: ChangeEvent):
    """
    HTTP shortcut for testing: POST a ChangeEvent JSON and get conflicts back
    without needing a WebSocket client. Also broadcasts any conflicts found.
    Useful for Person 1's test harness and Person 3's demo setup.
    """
    conflicts = detect_conflicts(event, graph)
    graph.apply_event(event.session_id, event.added, event.modified, event.deleted)

    enriched_list = []
    for raw_conflict in conflicts:
        enriched = await enrich_conflict(raw_conflict)
        await hub.broadcast(enriched.model_dump())
        enriched_list.append(enriched.model_dump())

    return {"conflicts_found": len(enriched_list), "conflicts": enriched_list}


@app.websocket("/ws/{session_id}")
async def ws_endpoint(websocket: WebSocket, session_id: str):
    await hub.connect(session_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            event = ChangeEvent.model_validate_json(raw)

            # Detect conflicts BEFORE updating graph so we see stale ownership.
            conflicts = detect_conflicts(event, graph)

            # Now update graph with the new state.
            graph.apply_event(event.session_id, event.added, event.modified, event.deleted)

            # For each conflict: enrich via AI layer, then broadcast.
            for raw_conflict in conflicts:
                enriched = await enrich_conflict(raw_conflict)
                await hub.broadcast(
                    enriched.model_dump(),
                    exclude_session=None,  # send to ALL sessions including sender
                )
    except WebSocketDisconnect:
        hub.disconnect(session_id)
    except Exception as e:
        hub.disconnect(session_id)
        raise e
