import json
import redis
from typing import Optional, Dict, Any

from app.core.config import settings

# Create a global redis client
redis_client = redis.from_url(settings.redis_url, decode_responses=True)

# 24 hour TTL for sessions
SESSION_TTL_SECONDS = 24 * 60 * 60

class SessionService:
    def __init__(self, client: redis.Redis):
        self.client = client
        self.prefix = "session:"

    def _key(self, identifier: str) -> str:
        return f"{self.prefix}{identifier}"

    def get_session(self, identifier: str) -> Dict[str, Any]:
        """Retrieve the session state for a given identifier."""
        data = self.client.get(self._key(identifier))
        if data:
            return json.loads(data)
        return {}

    def set_session(self, identifier: str, state: Dict[str, Any]) -> None:
        """Set the session state for a given identifier."""
        self.client.setex(
            self._key(identifier),
            SESSION_TTL_SECONDS,
            json.dumps(state)
        )

    def update_session(self, identifier: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update specific fields in the session state."""
        current_state = self.get_session(identifier)
        current_state.update(updates)
        self.set_session(identifier, current_state)
        return current_state

    def clear_session(self, identifier: str) -> None:
        """Clear the session state."""
        self.client.delete(self._key(identifier))

session_service = SessionService(redis_client)
