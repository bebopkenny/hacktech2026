"""
Posts a RawConflict to the AI layer and returns an EnrichedConflict.
Falls back gracefully if the AI layer is unreachable — send the raw reason as plain text.
"""
import os
import httpx
from models import RawConflict, EnrichedConflict

AI_LAYER_URL = os.getenv("AI_LAYER_URL", "http://localhost:8001")


async def enrich_conflict(raw: RawConflict) -> EnrichedConflict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{AI_LAYER_URL}/explain",
                json=raw.model_dump(),
            )
            resp.raise_for_status()
            data = resp.json()
            return EnrichedConflict(
                conflict_id=raw.conflict_id,
                severity=raw.severity,
                elements=raw.elements,
                plain_english=data["plain_english"],
                suggestion=data["suggestion"],
            )
    except Exception:
        # Degrade gracefully: surface the raw reason code so users still get an alert.
        return EnrichedConflict(
            conflict_id=raw.conflict_id,
            severity=raw.severity,
            elements=raw.elements,
            plain_english=f"Conflict detected: {raw.reason_code}",
            suggestion="Check with your collaborator before continuing.",
        )
