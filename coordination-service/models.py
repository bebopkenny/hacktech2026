"""
Canonical wire-format schemas. Import these in every service so the JSON
contract is defined in one place — not duplicated across plugin and server.
"""
from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class ElementSnapshot(BaseModel):
    element_id: int
    category: str = "Unknown"
    level: str | None = None
    host_id: int | None = None  # e.g. wall that hosts a door


class ChangeEvent(BaseModel):
    session_id: str
    document: str
    timestamp: datetime
    added: list[ElementSnapshot] = []
    modified: list[ElementSnapshot] = []
    deleted: list[int] = []


class RawConflict(BaseModel):
    conflict_id: str
    severity: Literal["warning", "error"]
    elements: list[int]          # element IDs involved
    reason_code: str             # machine-readable, e.g. "host_modified"
    context: dict                # extra fields for the AI prompt


class EnrichedConflict(BaseModel):
    conflict_id: str
    severity: Literal["warning", "error"]
    elements: list[int]
    plain_english: str           # filled in by AI layer
    suggestion: str              # filled in by AI layer
