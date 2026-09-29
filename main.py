
from collections import defaultdict, deque
from time import monotonic

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    auth,
    users,
    groups,
    contributions,
    loans,
    repayments,
    reports,
    finance,
)


def parse_rate(value: str) -> tuple[int, int]:
    try:
        n, unit = value.split("/", 1)
        seconds = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400,
        }[unit.rstrip("s").lower()]

        limit = int(n)

        if limit <= 0:
            raise ValueError

        return limit, seconds

    except (ValueError, KeyError) as exc:
        raise RuntimeError(
            "RATE_LIMIT must look like '100/minute'."
        ) from exc


_LIMIT, _WINDOW = parse_rate(settings.rate_limit)
_hits = defaultdict(deque)


def rate_limit(request: Request):
    if request.method == "OPTIONS" or request.url.path.startswith(
        ("/docs", "/openapi.json")
    ):
        return None

    key = (
        f"{request.client.host if request.client else 'unknown'}:"
        f"{request.url.path}"
    )

    now = monotonic()
    queue = _hits[key]

    while queue and queue[0] <= now - _WINDOW:
        queue.popleft()

    if len(queue) >= _LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
        )

    queue.append(now)

    return None


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    dependencies=[Depends(rate_limit)],
)

configured_origins = [
    origin.strip()
    for origin in settings.frontend_url.split(",")
    if origin.strip()
]

allowed_origins = list(
    dict.fromkeys(
        configured_origins
        + [
            "http://localhost:3000",
        ]
    )
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(groups.router, prefix="/api/v1")
app.include_router(contributions.router, prefix="/api/v1")
app.include_router(loans.router, prefix="/api/v1")
app.include_router(repayments.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(finance.router, prefix="/api/v1")

