import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import models
from .core.config import settings
from .core.database import Base, SessionLocal, engine
from .routers import admin, assignments, auth, patient_session, patients, questionnaires, statistics
from .seed import seed_database


def initialize_database() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_database(db)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id(request: Request, call_next):
    rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    detail = exc.detail
    message = detail if isinstance(detail, str) else detail.get("message", "请求处理失败")
    body = {"code": f"HTTP_{exc.status_code}", "message": message, "request_id": request.state.request_id}
    if isinstance(detail, dict) and "errors" in detail:
        body["errors"] = detail["errors"]
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={
        "code": "VALIDATION_ERROR", "message": "请求参数校验失败",
        "errors": exc.errors(), "request_id": request.state.request_id,
    })


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}


for router in [auth.router, patients.router, questionnaires.router, assignments.router, patient_session.router, statistics.router, admin.router]:
    app.include_router(router, prefix=settings.api_prefix)
