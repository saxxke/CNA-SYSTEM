"""
models.py
=========
Centralized authentication and user data models.

Required fields:
- user_id: Unique string identifier
- username: Unique login handle (normalized, case-insensitive index)
- password_hash: Cryptographic PBKDF2 hash (NEVER plaintext)
- role: One of the 4 supported UserRole enum values
- display_name: Human-friendly designation
- active: Boolean account status flag
- jurisdiction: Optional operational jurisdiction (e.g. Police Station, District, State, or National)
"""

from datetime import datetime, timezone
import re
from typing import Optional, Dict, Any, Union, List
from pydantic import BaseModel, Field, field_validator, ConfigDict

from .roles import UserRole, validate_role
from .security import verify_password, hash_password, parse_hash_string


USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.-]{3,50}$")


class User(BaseModel):
    """
    Core User entity model.
    Stores user credentials with securely hashed passwords.
    """
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    user_id: str = Field(..., description="Unique alphanumeric identifier for the user account.")
    username: str = Field(..., description="Unique login handle (case-insensitive in matching).")
    password_hash: str = Field(..., description="PBKDF2-HMAC-SHA256 password hash. Never store plaintext.")
    role: UserRole = Field(..., description="One of CITIZEN, INVESTIGATING_OFFICER, IPS_OFFICER, HOME_MINISTRY.")
    display_name: str = Field(..., description="Human-readable display name for the user.")
    active: bool = Field(default=True, description="Indicates whether the account is currently active.")
    jurisdiction: Optional[str] = Field(default=None, description="Operational jurisdiction or geographical scope.")
    jurisdiction_level: Optional[str] = Field(default=None, description="Scope level: DISTRICT, STATE, NATIONAL.")
    assigned_cases: Optional[List[str]] = Field(default_factory=list, description="Active assigned case IDs.")
    created_at: Optional[str] = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC creation timestamp."
    )
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Extensible non-sensitive user metadata.")

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("user_id cannot be empty or whitespace.")
        return v.strip()

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("username must be a string.")
        trimmed = v.strip()
        if not USERNAME_REGEX.match(trimmed):
            raise ValueError(
                f"Invalid username '{trimmed}'. Username must be 3-50 characters long "
                f"and contain only alphanumeric characters, dots, underscores, or hyphens."
            )
        return trimmed

    @field_validator("role", mode="before")
    @classmethod
    def validate_role_field(cls, v: Any) -> UserRole:
        return validate_role(v)

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("display_name cannot be empty.")
        return v.strip()

    @field_validator("password_hash")
    @classmethod
    def validate_password_hash(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("password_hash cannot be empty.")
        # Ensure it conforms to pbkdf2_sha256 format
        try:
            parse_hash_string(v)
        except Exception as e:
            raise ValueError(f"Invalid password_hash format: {e}")
        return v.strip()

    def check_password(self, plain_password: str) -> bool:
        """
        Verifies a plaintext candidate password against this user's hash.
        """
        return verify_password(plain_password, self.password_hash)

    def to_public(self) -> "UserPublic":
        """
        Converts the User model to a safe public representation without credentials.
        """
        assigned = self.assigned_cases or []
        return UserPublic(
            user_id=self.user_id,
            username=self.username,
            role=self.role,
            display_name=self.display_name,
            active=self.active,
            jurisdiction=self.jurisdiction,
            jurisdiction_level=self.jurisdiction_level,
            assigned_cases=assigned,
            assigned_cases_count=len(assigned),
            created_at=self.created_at
        )


class UserPublic(BaseModel):
    """
    Public / non-sensitive projection of User data suitable for APIs,
    session tokens, and investigator UI rendering.
    """
    model_config = ConfigDict(extra="forbid")

    user_id: str
    username: str
    role: UserRole
    display_name: str
    active: bool
    jurisdiction: Optional[str] = None
    jurisdiction_level: Optional[str] = None
    assigned_cases: Optional[List[str]] = None
    assigned_cases_count: Optional[int] = 0
    created_at: Optional[str] = None


class UserCreate(BaseModel):
    """
    Data transfer model for registering or creating a new user account.
    Accepts a plaintext password which is immediately hashed on conversion.
    """
    model_config = ConfigDict(extra="forbid")

    user_id: Optional[str] = None
    username: str
    password: str
    role: Union[UserRole, str]
    display_name: str
    active: bool = True
    jurisdiction: Optional[str] = None
    jurisdiction_level: Optional[str] = None
    assigned_cases: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not isinstance(v, str) or len(v) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        return v

    def to_user(self, generated_id: Optional[str] = None) -> User:
        """
        Transforms this creation request into a persistent User entity with
        a cryptographically hashed password. Plaintext password is not retained.
        """
        final_user_id = self.user_id or generated_id or f"usr_{secrets_token()}"
        hashed = hash_password(self.password)
        parsed_role = validate_role(self.role)
        return User(
            user_id=final_user_id,
            username=self.username,
            password_hash=hashed,
            role=parsed_role,
            display_name=self.display_name,
            active=self.active,
            jurisdiction=self.jurisdiction,
            metadata=self.metadata or {}
        )


def secrets_token() -> str:
    import secrets
    return secrets.token_hex(6)
