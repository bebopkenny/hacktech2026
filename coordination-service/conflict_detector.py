"""
Inspects an incoming ChangeEvent against the current graph state and returns
a list of RawConflict objects. No I/O — pure logic, easy to unit-test.
"""
import uuid
from models import ChangeEvent, ElementSnapshot, RawConflict
from dependency_graph import DependencyGraph


def detect_conflicts(event: ChangeEvent, graph: DependencyGraph) -> list[RawConflict]:
    conflicts: list[RawConflict] = []
    sender = event.session_id

    for snap in event.modified + [ElementSnapshot(element_id=eid, category="Unknown")
                                   for eid in event.deleted]:
        # Check: does any other session own a child of this element?
        for child in graph.get_hosted_children(snap.element_id):
            if child.owner_session != sender:
                conflicts.append(RawConflict(
                    conflict_id=f"cf-{uuid.uuid4().hex[:8]}",
                    severity="error",
                    elements=[snap.element_id, child.element_id],
                    reason_code="host_modified_while_child_owned_by_other",
                    context={
                        "acting_session": sender,
                        "child_owner": child.owner_session,
                        "host_category": snap.category,
                        "child_category": child.category,
                        "host_id": snap.element_id,
                        "child_id": child.element_id,
                    },
                ))

        # Check: is this element owned by a *different* session already?
        current_owner = graph.owner_of(snap.element_id)
        if current_owner and current_owner != sender:
            conflicts.append(RawConflict(
                conflict_id=f"cf-{uuid.uuid4().hex[:8]}",
                severity="warning",
                elements=[snap.element_id],
                reason_code="element_owned_by_other_session",
                context={
                    "acting_session": sender,
                    "owning_session": current_owner,
                    "element_id": snap.element_id,
                    "category": snap.category,
                },
            ))

    return conflicts
