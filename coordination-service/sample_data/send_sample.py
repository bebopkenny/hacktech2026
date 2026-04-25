"""
Replays sample_events.json against a running coordination service.
Usage:  python sample_data/send_sample.py
Useful for Person 2 to test the full pipeline without a Revit instance.
"""
import asyncio
import json
import pathlib
import websockets

EVENTS_FILE = pathlib.Path(__file__).parent / "sample_events.json"
WS_BASE = "ws://localhost:8000/ws"


async def main():
    events = json.loads(EVENTS_FILE.read_text())

    # Open one connection per unique session_id in the sample data.
    sessions = {e["session_id"] for e in events}
    connections = {}
    for sid in sessions:
        connections[sid] = await websockets.connect(f"{WS_BASE}/{sid}")
        print(f"Connected session: {sid}")

    for event in events:
        comment = event.pop("comment", "")
        sid = event["session_id"]
        print(f"\nSending [{sid}]: {comment}")
        await connections[sid].send(json.dumps(event))
        await asyncio.sleep(0.2)

    # Listen briefly for any broadcast messages.
    print("\nListening for broadcasts (3s)...")
    for sid, ws in connections.items():
        ws.close_timeout = 0
    await asyncio.sleep(3)

    for ws in connections.values():
        await ws.close()


asyncio.run(main())
