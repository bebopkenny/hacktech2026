"""
Unit tests for dependency_graph.py.
"""
from dependency_graph import DependencyGraph
from models import ElementSnapshot


def _snap(element_id, category="Walls", level="L1", host_id=None):
    return ElementSnapshot(element_id=element_id, category=category,
                           level=level, host_id=host_id)


def test_apply_event_adds_nodes():
    g = DependencyGraph()
    g.apply_event("user-1", added=[_snap(1), _snap(2)], modified=[], deleted=[])
    assert g.owner_of(1) == "user-1"
    assert g.owner_of(2) == "user-1"


def test_ownership_transfers_on_modify():
    g = DependencyGraph()
    g.apply_event("user-1", added=[_snap(1)], modified=[], deleted=[])
    g.apply_event("user-2", added=[], modified=[_snap(1)], deleted=[])
    assert g.owner_of(1) == "user-2"


def test_delete_removes_node():
    g = DependencyGraph()
    g.apply_event("user-1", added=[_snap(1)], modified=[], deleted=[])
    g.apply_event("user-1", added=[], modified=[], deleted=[1])
    assert g.owner_of(1) is None


def test_get_hosted_children():
    g = DependencyGraph()
    g.apply_event("user-2",
        added=[_snap(10, "Walls"), _snap(20, "Doors", host_id=10), _snap(30, "Doors", host_id=10)],
        modified=[], deleted=[])
    children = g.get_hosted_children(10)
    assert {c.element_id for c in children} == {20, 30}


def test_no_children_for_unknown_host():
    g = DependencyGraph()
    assert g.get_hosted_children(999) == []


def test_elements_on_level():
    g = DependencyGraph()
    g.apply_event("user-1",
        added=[_snap(1, level="L1"), _snap(2, level="L2"), _snap(3, level="L1")],
        modified=[], deleted=[])
    on_l1 = g.get_elements_on_level("L1")
    assert {e.element_id for e in on_l1} == {1, 3}
