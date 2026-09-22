from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from backend.agents.supervisor import route_request
from backend.config import APP_NAME, MAX_MESSAGE_LENGTH
from backend.rag.hybrid_search import search_documents
from backend.security.auth import User, get_user, login
from backend.security.guardrails import find_prompt_injection
from backend.security.rate_limiter import TokenBucketRateLimiter


app = FastAPI(title=APP_NAME)
rate_limiter = TokenBucketRateLimiter()
MEMORY: dict[str, list[dict[str, str]]] = {}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    role: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)


class Citation(BaseModel):
    document_id: str
    title: str
    source: str


class ChatResponse(BaseModel):
    answer: str
    route: str
    citations: list[Citation]
    activity: list[str]
    history_length: int


def current_user(authorization: str = Header(default="")) -> User:
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    user = get_user(authorization.removeprefix(prefix))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": APP_NAME}


@app.post("/login", response_model=LoginResponse)
async def login_endpoint(payload: LoginRequest) -> LoginResponse:
    result = login(payload.username, payload.password)
    if result is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token, user = result
    MEMORY[token] = []
    return LoginResponse(token=token, username=user.username, role=user.role)


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, user: User = Depends(current_user), authorization: str = Header(default="")) -> ChatResponse:
    token = authorization.removeprefix("Bearer ")

    if not rate_limiter.allow(user.username):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    suspicious_pattern = find_prompt_injection(payload.message)
    if suspicious_pattern:
        activity = [
            "Request validated",
            "Prompt-injection guardrail detected a suspicious instruction",
            "Request blocked before retrieval",
        ]
        return ChatResponse(
            answer="I cannot help with requests that try to bypass instructions, reveal hidden prompts, or access unauthorized data.",
            route="blocked",
            citations=[],
            activity=activity,
            history_length=len(MEMORY.get(token, [])),
        )

    route, activity = route_request(payload.message, user.role)
    if route == "forbidden_analysis":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your role cannot run analysis tools")

    chunks = search_documents(payload.message, user.role, limit=6 if route == "analysis" else 4)
    activity.append("Knowledge search completed")
    activity.append(f"Retrieved {len(chunks)} authorized chunks")

    if not chunks:
        answer = "I could not find supporting evidence in the available documents for your role."
        citations: list[Citation] = []
    elif route == "analysis":
        activity.append("Analysis agent grouped retrieved evidence")
        root_causes = "; ".join(chunk.title for chunk in chunks[:3])
        answer = (
            "Based on the available incident evidence, the recurring themes are database capacity, "
            f"payment dependency timeouts, and operational recovery steps. Most relevant sources: {root_causes}."
        )
        citations = [Citation(document_id=c.document_id, title=c.title, source=c.source) for c in chunks]
    else:
        activity.append("Response agent generated grounded answer")
        evidence = "\n\n".join(f"{chunk.title}: {chunk.content}" for chunk in chunks[:2])
        answer = f"Based on the available documents:\n\n{evidence}"
        citations = [Citation(document_id=c.document_id, title=c.title, source=c.source) for c in chunks]

    MEMORY.setdefault(token, []).extend(
        [
            {"role": "user", "content": payload.message},
            {"role": "assistant", "content": answer},
        ]
    )
    activity.append("Session memory updated")

    return ChatResponse(
        answer=answer,
        route=route,
        citations=citations,
        activity=activity,
        history_length=len(MEMORY[token]),
    )
