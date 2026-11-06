"""
DisasterSafe Session Manager
In-memory thread-safe session tracking for user conversations, path history,
undo/back support, tag aggregation, and privacy-friendly anonymous analytics.
"""

import time
import uuid
from typing import Dict, List, Optional, Any, Set


class Session:
    def __init__(self, session_id: str, hazard_id: str, lang: str = "en"):
        self.session_id: str = session_id
        self.hazard_id: str = hazard_id
        self.lang: str = lang
        self.current_node_id: Optional[str] = None
        self.path_history: List[str] = []
        self.step_history: List[Dict[str, Any]] = []  # For undo/back
        self.answers: List[Dict[str, Any]] = []
        self.collected_tags: Set[str] = set()
        self.is_complete: bool = False
        self.summary: Optional[Dict[str, Any]] = None
        self.created_at: float = time.time()
        self.updated_at: float = time.time()

    def snapshot(self) -> Dict[str, Any]:
        """Creates a state snapshot for undo support."""
        return {
            "current_node_id": self.current_node_id,
            "path_history": list(self.path_history),
            "answers": list(self.answers),
            "collected_tags": set(self.collected_tags),
            "is_complete": self.is_complete
        }

    def restore_snapshot(self, snap: Dict[str, Any]):
        """Restores a previous state snapshot."""
        self.current_node_id = snap["current_node_id"]
        self.path_history = list(snap["path_history"])
        self.answers = list(snap["answers"])
        self.collected_tags = set(snap["collected_tags"])
        self.is_complete = snap["is_complete"]
        self.summary = None
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "hazard_id": self.hazard_id,
            "lang": self.lang,
            "current_node_id": self.current_node_id,
            "path_history": self.path_history,
            "answers_count": len(self.answers),
            "is_complete": self.is_complete,
            "tags": list(self.collected_tags),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class SessionManager:
    def __init__(self, max_sessions: int = 5000, ttl_seconds: int = 86400):
        self.sessions: Dict[str, Session] = {}
        self.max_sessions = max_sessions
        self.ttl_seconds = ttl_seconds
        # Anonymous aggregate analytics counters
        self.analytics = {
            "total_conversations": 0,
            "completed_conversations": 0,
            "hazard_counts": {"flood": 0, "earthquake": 0, "landslide": 0},
            "language_counts": {"en": 0, "ml": 0, "hi": 0},
            "path_frequencies": {}
        }

    def create_session(self, hazard_id: str, lang: str = "en") -> Session:
        self._cleanup_expired()
        session_id = str(uuid.uuid4())
        session = Session(session_id, hazard_id, lang)
        self.sessions[session_id] = session

        # Track analytics
        self.analytics["total_conversations"] += 1
        self.analytics["hazard_counts"][hazard_id] = self.analytics["hazard_counts"].get(hazard_id, 0) + 1
        self.analytics["language_counts"][lang] = self.analytics["language_counts"].get(lang, 0) + 1

        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        if not session_id:
            return None
        session = self.sessions.get(session_id)
        if session:
            # Check TTL
            if time.time() - session.updated_at > self.ttl_seconds:
                del self.sessions[session_id]
                return None
            session.updated_at = time.time()
        return session

    def pop_step(self, session_id: str) -> Optional[Session]:
        """Undoes the last action step, returning to the previous question."""
        session = self.get_session(session_id)
        if not session or not session.step_history:
            return None
        prev_snap = session.step_history.pop()
        session.restore_snapshot(prev_snap)
        return session

    def mark_completed(self, session_id: str, summary: Dict[str, Any]):
        session = self.get_session(session_id)
        if session:
            session.is_complete = True
            session.summary = summary
            self.analytics["completed_conversations"] += 1
            path_key = " -> ".join(session.path_history)
            self.analytics["path_frequencies"][path_key] = self.analytics["path_frequencies"].get(path_key, 0) + 1

    def _cleanup_expired(self):
        now = time.time()
        expired = [sid for sid, s in self.sessions.items() if now - s.updated_at > self.ttl_seconds]
        for sid in expired:
            del self.sessions[sid]

        if len(self.sessions) > self.max_sessions:
            # Evict oldest
            oldest = sorted(self.sessions.items(), key=lambda x: x[1].updated_at)[:500]
            for sid, _ in oldest:
                del self.sessions[sid]

    def get_analytics(self) -> Dict[str, Any]:
        total = self.analytics["total_conversations"]
        completed = self.analytics["completed_conversations"]
        rate = round((completed / total * 100), 1) if total > 0 else 0.0

        # Most common paths
        top_paths = sorted(
            self.analytics["path_frequencies"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            "total_conversations": total,
            "completed_conversations": completed,
            "completion_rate": rate,
            "hazard_counts": self.analytics["hazard_counts"],
            "language_counts": self.analytics["language_counts"],
            "top_paths": [{"path": p, "count": c} for p, c in top_paths],
            "active_sessions_count": len(self.sessions)
        }


# Global default instance
session_manager = SessionManager()

