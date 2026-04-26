"""Fire a sample conflict toast — useful for verifying the UI without touching the server."""
from revitsync import notifications

notifications.show({
    "conflict_id": "test-001",
    "severity": "warning",
    "elements": [123, 456],
    "plain_english": "You moved Wall #123, but Person B's Door #456 is hosted on it.",
    "suggestion": "Coordinate with Person B before committing, or rehost the door.",
})
