"""In-memory session store — no database needed for MVP."""

from models import SessionState

# Singleton session store keyed by session_id
sessions: dict[str, SessionState] = {}


def save_session(session: SessionState) -> None:
    """Insert or update a session."""
    sessions[session.session_id] = session


def get_session(session_id: str) -> SessionState | None:
    """Retrieve a session by ID, or None if not found."""
    return sessions.get(session_id)
