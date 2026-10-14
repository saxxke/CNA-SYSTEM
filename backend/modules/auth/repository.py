"""
repository.py
=============
Centralized User Store / Repository.

Features:
- Thread-safe in-memory user registry.
- Strict uniqueness enforcement for `user_id` and case-insensitive `username`.
- Active / Inactive user filtering.
- Complete decoupling from synthetic criminal network data CSVs.
- Ready for future session/token authentication and RBAC middlewares.
"""

from threading import RLock
from typing import Dict, List, Optional
from .models import User


class UserRepository:
    """
    In-memory repository managing User identities.
    Keeps authentication entities strictly decoupled from investigation dataset.
    """

    def __init__(self):
        self._lock = RLock()
        self._users_by_id: Dict[str, User] = {}
        self._id_by_username_lower: Dict[str, str] = {}

    def add_user(self, user: User) -> User:
        """
        Adds a new user to the repository.
        Raises ValueError if user_id or username already exists.
        """
        if not isinstance(user, User):
            raise TypeError("Expected User instance.")

        uname_key = user.username.strip().lower()
        uid_key = user.user_id.strip()

        with self._lock:
            if uid_key in self._users_by_id:
                raise ValueError(f"User ID '{user.user_id}' already exists.")
            if uname_key in self._id_by_username_lower:
                existing_id = self._id_by_username_lower[uname_key]
                existing = self._users_by_id.get(existing_id)
                existing_name = existing.username if existing else uname_key
                raise ValueError(f"Username '{existing_name}' already exists (case-insensitive collision).")

            self._users_by_id[uid_key] = user
            self._id_by_username_lower[uname_key] = uid_key
            return user

    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieves a user by user_id. Returns None if not found.
        """
        if not user_id:
            return None
        with self._lock:
            return self._users_by_id.get(user_id.strip())

    def get_by_username(self, username: str) -> Optional[User]:
        """
        Retrieves a user by username (case-insensitive). Returns None if not found.
        """
        if not username:
            return None
        uname_key = username.strip().lower()
        with self._lock:
            uid = self._id_by_username_lower.get(uname_key)
            if uid:
                return self._users_by_id.get(uid)
            return None

    def get_active_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieves a user by username only if the account is active.
        Returns None if user is not found or is deactivated.
        """
        user = self.get_by_username(username)
        if user and user.active:
            return user
        return None

    def is_user_active(self, username_or_id: str) -> bool:
        """
        Checks whether the specified user exists and is currently active.
        """
        user = self.get_by_id(username_or_id) or self.get_by_username(username_or_id)
        return bool(user and user.active)

    def deactivate_user(self, user_id_or_username: str) -> bool:
        """
        Marks a user account as inactive.
        Returns True if successful, False if user not found.
        """
        with self._lock:
            user = self.get_by_id(user_id_or_username) or self.get_by_username(user_id_or_username)
            if not user:
                return False
            # Pydantic validate_assignment=True allows updating active
            user.active = False
            return True

    def activate_user(self, user_id_or_username: str) -> bool:
        """
        Marks a user account as active.
        Returns True if successful, False if user not found.
        """
        with self._lock:
            user = self.get_by_id(user_id_or_username) or self.get_by_username(user_id_or_username)
            if not user:
                return False
            user.active = True
            return True

    def list_users(self, include_inactive: bool = True) -> List[User]:
        """
        Returns all registered users.
        """
        with self._lock:
            users = list(self._users_by_id.values())
            if not include_inactive:
                users = [u for u in users if u.active]
            return users

    def count(self) -> int:
        with self._lock:
            return len(self._users_by_id)

    def clear(self) -> None:
        """
        Clears all users from repository (useful for test resets).
        """
        with self._lock:
            self._users_by_id.clear()
            self._id_by_username_lower.clear()

