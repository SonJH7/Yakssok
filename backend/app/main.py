from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.base import Base
from app.db.session import engine
from app.routes import calendar_route, user_route, appointment_route
from app.services.google_calendar_service import GoogleCalendarService
from app.variable import FRONTEND_URL


def _resolve_allowed_origins(frontend_url: str) -> list[str]:
    if not frontend_url:
        return []

    parsed = urlparse(frontend_url)

    if parsed.scheme and parsed.netloc:
        return [f"{parsed.scheme}://{parsed.netloc}"]

    return [frontend_url]


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=_resolve_allowed_origins(FRONTEND_URL),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("shutdown")
async def shutdown():
    await GoogleCalendarService.close_client()


app.include_router(user_route.router, tags=["user"])
app.include_router(calendar_route.router, tags=["calendar"])
app.include_router(appointment_route.router, tags=["appointment"])
