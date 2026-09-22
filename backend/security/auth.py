from dataclasses import dataclass
from typing import Optional
from uuid import uuid4


@dataclass(frozen=True)
class User:
    username: str
    role: str


USERS = {
    "viewer": {"password": "viewer123", "role": "viewer"},
    "analyst": {"password": "analyst123", "role": "analyst"},
    "admin": {"password": "admin123", "role": "admin"},
}

SESSIONS: dict[str, User] = {}


def login(username: str, password: str) -> Optional[tuple[str, User]]:
    normalized_username = (username or "").strip()
    normalized_password = (password or "").strip()
    if not normalized_username or not normalized_password:
        return None

    record = USERS.get(normalized_username)
    if not record or record["password"] != normalized_password:
        return None

    token = str(uuid4())
    user = User(username=normalized_username, role=record["role"])
    SESSIONS[token] = user
    return token, user


def get_user(token: str) -> Optional[User]:
    return SESSIONS.get(token)


def allowed_access_levels(role: str) -> set[str]:
    normalized_role = (role or "").lower().strip()
    if normalized_role == "admin":
        return {"public", "internal", "restricted"}
    return {"public", "internal"}


def can_run_analysis(role: str) -> bool:
    normalized_role = (role or "").lower().strip()
    return normalized_role in {"analyst", "admin"}
