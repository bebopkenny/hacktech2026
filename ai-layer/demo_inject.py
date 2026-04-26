"""
Demo trigger — fires the flagship conflict scenario through the full pipeline:
  Kenny owns door 200 (hosted on wall 100).
  James moves wall 100.
  → Conflict detected → K2 enriches it → broadcasts to Three.js UI.

Run order (three separate terminals):
  1. cd coordination-service && python3 -m uvicorn main:app --port 8000
  2. cd ai-layer       && python3 -m uvicorn main:app --port 8001
  3. Open ui/threejs-demo/index.html in your browser
  4. cd ai-layer       && python3 demo_inject.py

The Three.js demo should display the conflict card and flash elements 100 + 200 red.
Run this script multiple times to re-trigger the scenario.
"""

import httpx
from datetime import datetime, timezone

COORD_URL = "http://localhost:8000"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main():
    with httpx.Client(timeout=20.0) as client:

        # Step 1: Seed — Kenny registers door 200 as hosted on wall 100.
        # No conflict fires here because James hasn't touched anything yet.
        print("Step 1: Seeding Kenny's door (element 200) on wall 100...")
        seed = {
            "session_id": "kenny",
            "document": "demo-model",
            "timestamp": _now(),
            "added": [{"element_id": 200, "category": "Doors", "host_id": 100}],
            "modified": [],
            "deleted": [],
        }
        r = client.post(f"{COORD_URL}/inject", json=seed)
        r.raise_for_status()
        print(f"  OK ({r.json()['conflicts_found']} conflicts — expected 0)\n")

        # Step 2: Trigger — James modifies wall 100.
        # Conflict detector sees Kenny owns a door hosted on that wall → fires conflict.
        # Coordination service calls AI layer (K2) → broadcasts EnrichedConflict to Three.js.
        print("Step 2: James moves wall 100...")
        trigger = {
            "session_id": "james",
            "document": "demo-model",
            "timestamp": _now(),
            "added": [],
            "modified": [{"element_id": 100, "category": "Walls"}],
            "deleted": [],
        }
        r = client.post(f"{COORD_URL}/inject", json=trigger)
        r.raise_for_status()
        data = r.json()

        print(f"  Conflicts found: {data['conflicts_found']}")
        for c in data.get("conflicts", []):
            print(f"\n  PLAIN EN : {c['plain_english']}")
            print(f"  SUGGEST  : {c['suggestion']}")
            print(f"  ELEMENTS : {c['elements']}")
            print(f"  SEVERITY : {c['severity']}")

        if data["conflicts_found"] == 0:
            print("\n  No conflicts detected — make sure the coordination service is running.")


if __name__ == "__main__":
    main()
