"""
Unit tests for conflict_detector.py — no network, no Revit, no AI layer.
Person 2 can run these while building the service logic.

    cd coordination-service && pytest tests/ -v
"""
from datetime import datetime, timezone
import pytest
from models import ChangeEvent, ElementSnapshot
from dependency_graph import DependencyGraph
from conflict_detector import detect_conflicts


def _event(session_id: str, added=None, modified=None, deleted=None) -> ChangeEvent:
    return ChangeEvent(
        session_id=session_id,
        document="test.rvt",
        timestamp=datetime.now(timezone.utc),
        added=added or [],
        modified=modified or [],
        deleted=deleted or [],
    )


def _snap(element_id: int, category="Walls", level="L1", host_id=None) -> ElementSnapshot:
    return ElementSnapshot(element_id=element_id, category=category,
                           level=level, host_id=host_id)


# ---------------------------------------------------------------------------
# Host / child conflict
# ---------------------------------------------------------------------------

class TestHostModifiedConflict:
    def setup_method(self):
        self.graph = DependencyGraph()

    def test_wall_moved_while_other_session_owns_door(self):
        # user-2 adds a door hosted on wall 100
        self.graph.apply_event("user-2",
            added=[_snap(100, "Walls"), _snap(200, "Doors", host_id=100)],
            modified=[], deleted=[])

        # user-1 moves the wall
        event = _event("user-1", modified=[_snap(100, "Walls")])
        conflicts = detect_conflicts(event, self.graph)

        assert len(conflicts) == 1
        c = conflicts[0]
        assert c.reason_code == "host_modified_while_child_owned_by_other"
        assert c.severity == "error"
        assert 100 in c.elements
        assert 200 in c.elements
        assert c.context["acting_session"] == "user-1"
        assert c.context["child_owner"] == "user-2"

    def test_no_conflict_when_same_session_owns_child(self):
        self.graph.apply_event("user-1",
            added=[_snap(100, "Walls"), _snap(200, "Doors", host_id=100)],
            modified=[], deleted=[])

        event = _event("user-1", modified=[_snap(100, "Walls")])
        conflicts = detect_conflicts(event, self.graph)
        assert conflicts == []

    def test_wall_deleted_triggers_conflict(self):
        self.graph.apply_event("user-2",
            added=[_snap(100, "Walls"), _snap(200, "Doors", host_id=100)],
            modified=[], deleted=[])

        event = _event("user-1", deleted=[100])
        conflicts = detect_conflicts(event, self.graph)

        assert any(c.reason_code == "host_modified_while_child_owned_by_other"
                   for c in conflicts)


# ---------------------------------------------------------------------------
# Concurrent edit conflict
# ---------------------------------------------------------------------------

class TestConcurrentEditConflict:
    def setup_method(self):
        self.graph = DependencyGraph()

    def test_modifying_element_owned_by_other_session(self):
        self.graph.apply_event("user-2",
            added=[_snap(500, "Structural Columns")],
            modified=[], deleted=[])

        event = _event("user-1", modified=[_snap(500, "Structural Columns")])
        conflicts = detect_conflicts(event, self.graph)

        assert any(c.reason_code == "element_owned_by_other_session" for c in conflicts)
        c = next(c for c in conflicts if c.reason_code == "element_owned_by_other_session")
        assert c.severity == "warning"
        assert c.context["owning_session"] == "user-2"

    def test_no_conflict_on_fresh_element(self):
        event = _event("user-1", added=[_snap(999, "Windows")])
        conflicts = detect_conflicts(event, self.graph)
        assert conflicts == []


# ---------------------------------------------------------------------------
# Multi-conflict scenario
# ---------------------------------------------------------------------------

def test_multiple_conflicts_in_one_event():
    graph = DependencyGraph()
    # user-2 owns two things: a wall and a door hosted on it
    graph.apply_event("user-2",
        added=[_snap(10, "Walls"), _snap(20, "Doors", host_id=10)],
        modified=[], deleted=[])
    # user-3 owns a column
    graph.apply_event("user-3",
        added=[_snap(30, "Structural Columns")],
        modified=[], deleted=[])

    # user-1 modifies both the wall and the column in one event
    event = _event("user-1",
        modified=[_snap(10, "Walls"), _snap(30, "Structural Columns")])
    conflicts = detect_conflicts(event, graph)

    reason_codes = {c.reason_code for c in conflicts}
    assert "host_modified_while_child_owned_by_other" in reason_codes
    assert "element_owned_by_other_session" in reason_codes
