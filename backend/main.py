import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from core.config import get_settings
from core.database import init_db
from routes import analysis, auth, dashboard
from services.model_loader import model_loader


settings = get_settings()
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("ai-lung-scan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    (settings.uploads_dir / "originals").mkdir(parents=True, exist_ok=True)
    (settings.uploads_dir / "heatmaps").mkdir(parents=True, exist_ok=True)
    init_db()
    model_loader.load_models()
    logger.info(
        "Application started. available_models=%s unavailable_models=%s",
        [model.key for model in model_loader.available_models()],
        [model.key for model in model_loader.unavailable_models()],
    )
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def request_logger(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %s %.2fms", request.method, request.url.path, response.status_code, elapsed_ms)
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": str(exc.detail), "error": str(exc.detail)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"success": False, "message": "So'rov ma'lumotlari noto'g'ri", "error": exc.errors()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Serverda kutilmagan xatolik yuz berdi", "error": str(exc)},
    )


app.mount("/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(analysis.router, prefix=settings.api_prefix)
app.include_router(dashboard.router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return RedirectResponse(url="/login.html")


@app.get("/api/health")
def health():
    return {
        "success": True,
        "message": "AI Lung Scan API ishlayapti",
        "data": {
            "docs": "/docs",
            "available_models": [model.key for model in model_loader.available_models()],
            "unavailable_models": [model.key for model in model_loader.unavailable_models()],
        },
    }


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
