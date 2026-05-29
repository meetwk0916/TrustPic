import os

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.models import AnalyzeResponse
from app.services.analyze import AnalyzeError, analyze_upload

app = FastAPI(title="TrustPic API", version="0.1.0")

DEFAULT_ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


def allowed_origins() -> list[str]:
    raw = os.getenv("TRUSTPIC_ALLOWED_ORIGINS")
    if not raw:
        return DEFAULT_ALLOWED_ORIGINS
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def allowed_origin_regex() -> str | None:
    raw = os.getenv("TRUSTPIC_ALLOWED_ORIGIN_REGEX")
    return raw.strip() if raw else None


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_origin_regex=allowed_origin_regex(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze_image(file: UploadFile = File(...), locale: str = Query("zh-CN")) -> AnalyzeResponse:
    try:
        return await analyze_upload(file, locale=locale)
    except AnalyzeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
