"""
Standalone integration test for Person 1 — no Revit required.
Connects two fake sessions over WebSocket and replays a conflict scenario,
then listens for the enriched conflict broadcast.

Usage (from any machine with Python):
    pip install websockets
    python revit-plugin/test_harness.py [ws://localhost:8000/ws]
"""
import asyncio
import json
import sys
from datetime import datetime, timezone

import websockets

WS_BASE = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8000/ws"

SCENARIO = [
    # Step 1: user-1 adds a wall
    ("user-1", {
        "session_id": "user-1", "document": "test.rvt",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "added": [{"element_id": 100, "category": "Walls", "level": "L1"}],
        "modified": [], "deleted": [],
    }),
    # Step 2: user-2 adds a door hosted on that wall
    ("user-2", {
        "session_id": "user-2", "document": "test.rvt",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "added": [{"element_id": 200, "category": "Doors", "level": "L1", "host_id": 100}],
        "modified": [], "deleted": [],
    }),
    # Step 3: user-1 moves the wall — should trigger a conflict
    ("user-1", {
        "session_id": "user-1", "document": "test.rvt",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "added": [],
        "modified": [{"element_id": 100, "category": "Walls", "level": "L1"}],
        "deleted": [],
    }),
]


async def main():
    print(f"Connecting to {WS_BASE}")
    async with (
        websockets.connect(f"{WS_BASE}/user-1") as ws1,
        websockets.connect(f"{WS_BASE}/user-2") as ws2,
    ):
        sockets = {"user-1": ws1, "user-2": ws2}
        print("Both sessions connected.\n")

        for session_id, event in SCENARIO:
            print(f"[{session_id}] sending: {event['added'] and 'add' or event['modified'] and 'modify' or 'delete'} "
                  f"elements {[e['element_id'] for e in event['added'] + event['modified']] or event['deleted']}")
            await sockets[session_id].send(json.dumps(event))
            await asyncio.sleep(0.3)

        print("\nListening for conflict broadcasts (5s)...")
        try:
            async with asyncio.timeout(5):
                async for message in ws1:
                    conflict = json.loads(message)
                    print("\n=== CONFLICT RECEIVED ===")
                    print(f"  Severity : {conflict.get('severity')}")
                    print(f"  Elements : {conflict.get('elements')}")
                    print(f"  Message  : {conflict.get('plain_english')}")
                    print(f"  Suggest  : {conflict.get('suggestion')}")
        except TimeoutError:
            print("(no conflicts received in 5s)")

    print("\nDone.")


asyncio.run(main())
