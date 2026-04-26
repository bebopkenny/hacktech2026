"""Per-machine configuration. Override via environment variables set by install.ps1."""
import os

WS_URL     = os.getenv("REVITSYNC_WS_URL", "ws://107.191.50.160:8000/ws")
SESSION_ID = os.getenv("REVITSYNC_SESSION_ID", "user-1")

# Toast UI
TOAST_LIFETIME_S = int(os.getenv("REVITSYNC_TOAST_LIFETIME_S", "8"))
