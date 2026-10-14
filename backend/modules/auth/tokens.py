"""
tokens.py
=========
In-memory session and authentication token management.

Features:
- Cryptographically secure 256-bit URL-safe bearer tokens (secrets.token_urlsafe(32)).
- Thread-safe token storage and verification with RLock.
- Configurable expiration (default 24 hours).
- Immediate revocation upon logout.
- Invalidation of revoked or expired tokens.
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from threading import RLock
from typing import Dict, Optional, Set
import secrets

from .roles import UserRole
from .models import User


DEFAULT_TOKEN_EXPIRATION_HOURS = 24


@dataclass
class TokenSession:
    token: str
    user_id: str
    username: str
    role: UserRole
    created_at: datetime
    expires_at: datetime
    revoked: bool = False

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def is_active(self) -> bool:
        return (not self.revoked) and (not self.is_expired)


class TokenStore:
    """
    Thread-safe registry for active bearer tokens and user sessions.
    Decoupled from criminal network data and safe for multi-user test concurrency.
    """

    def __init__(self, expiration_hours: int = DEFAULT_TOKEN_EXPIRATION_HOURS):
        self._lock = RLock()
        self._expiration_delta = timedelta(hours=expiration_hours)
        self._sessions_by_token: Dict[str, TokenSession] = {}
        self._tokens_by_user_id: Dict[str, Set[str]] = {}

    def create_token(self, user: User, duration: Optional[timedelta] = None) -> TokenSession:
        """
        Generates a new secure token session for the given user.
        """
        if not isinstance(user, User):
            raise TypeError("Expected User entity to create token.")

        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = now + (duration if duration is not None else self._expiration_delta)

        session = TokenSession(
            token=token,
            user_id=user.user_id,
            username=user.username,
            role=user.role,
            created_at=now,
            expires_at=expires_at,
            revoked=False
        )

        with self._lock:
            self._sessions_by_token[token] = session
            if user.user_id not in self._tokens_by_user_id:
                self._tokens_by_user_id[user.user_id] = set()
            self._tokens_by_user_id[user.user_id].add(token)

        return session

    def get_session(self, token: str) -> Optional[TokenSession]:
        """
        Retrieves an active, non-revoked, non-expired token session.
        Returns None if invalid, revoked, or expired.
        """
        if not token or not isinstance(token, str):
            return None

        clean_token = token.strip()
        with self._lock:
            session = self._sessions_by_token.get(clean_token)
            if not session:
                return None
            if not session.is_active:
                return None
            return session

    def revoke_token(self, token: str) -> bool:
        """
        Revokes a specific token session immediately.
        Returns True if revoked, False if token did not exist.
        """
        if not token or not isinstance(token, str):
            return False

        clean_token = token.strip()
        with self._lock:
            session = self._sessions_by_token.get(clean_token)
            if not session:
                return False
            session.revoked = True
            # Remove from user set
            if session.user_id in self._tokens_by_user_id:
                self._tokens_by_user_id[session.user_id].discard(clean_token)
            return True

    def revoke_all_for_user(self, user_id: str) -> int:
        """
        Revokes all active tokens for a specific user ID.
        Returns count of revoked tokens.
        """
        if not user_id:
            return 0

        clean_uid = user_id.strip()
        revoked_count = 0
        with self._lock:
            tokens = list(self._tokens_by_user_id.get(clean_uid, set()))
            for t in tokens:
                s = self._sessions_by_token.get(t)
                if s and not s.revoked:
                    s.revoked = True
                    revoked_count += 1
            self._tokens_by_user_id.pop(clean_uid, None)
        return revoked_count

    def clear(self) -> None:
        """
        Clears all stored sessions.
        """
        with self._lock:
            self._sessions_by_token.clear()
            self._tokens_by_user_id.clear()

    def count_active(self) -> int:
        with self._lock:
            return sum(1 for s in self._sessions_by_token.values() if s.is_active)
