"""
Tracks element state and ownership across sessions.

The graph answers two questions:
  1. Does element X depend on element Y? (host/child, shared level)
  2. Which session currently owns element X?

Ownership = "the last session to touch this element."
"""
from dataclasses import dataclass, field
from models import ElementSnapshot


@dataclass
class ElementNode:
    element_id: int
    category: str
    level: str | None
    host_id: int | None
    owner_session: str


class DependencyGraph:
    def __init__(self):
        # element_id → ElementNode
        self._nodes: dict[int, ElementNode] = {}

    def apply_event(self, session_id: str, added: list[ElementSnapshot],
                    modified: list[ElementSnapshot], deleted: list[int]):
        for snap in added + modified:
            self._nodes[snap.element_id] = ElementNode(
                element_id=snap.element_id,
                category=snap.category,
                level=snap.level,
                host_id=snap.host_id,
                owner_session=session_id,
            )
        for eid in deleted:
            self._nodes.pop(eid, None)

    def get_hosted_children(self, host_id: int) -> list[ElementNode]:
        """Return all elements whose host_id matches the given element."""
        return [n for n in self._nodes.values() if n.host_id == host_id]

    def get_elements_on_level(self, level: str) -> list[ElementNode]:
        return [n for n in self._nodes.values() if n.level == level]

    def owner_of(self, element_id: int) -> str | None:
        node = self._nodes.get(element_id)
        return node.owner_session if node else None


# Module-level singleton.
graph = DependencyGraph()
