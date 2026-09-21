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
    record = USERS.get(username)
    if not record or record["password"] != password:
        return None

    token = str(uuid4())
    user = User(username=username, role=record["role"])
    SESSIONS[token] = user
    return token, user


def get_user(token: str) -> Optional[User]:
    return SESSIONS.get(token)


def allowed_access_levels(role: str) -> set[str]:
    if role == "admin":
        return {"public", "internal", "restricted"}
    if role == "analyst":
        return {"public", "internal", "restricted"}
    return {"public", "internal"}


def can_run_analysis(role: str) -> bool:
    return role in {"analyst", "admin"}
