from contextlib import asynccontextmanager
import os
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(os.path.join(UPLOAD_DIR, "images"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "videos"), exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        description="House Rental System backend built with FastAPI",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

    app.include_router(api_router, prefix="/api/v1")

    @app.post("/api/v1/upload", tags=["upload"])
    async def upload_file(file: UploadFile = File(...)):
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp", "video/mp4", "video/webm"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type not allowed")
        if file.content_type.startswith("image/"):
            sub_dir = "images"
        else:
            sub_dir = "videos"
        ext = os.path.splitext(file.filename)[1] if file.filename else ""
        filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_DIR, sub_dir, filename)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 10MB)")
        with open(file_path, "wb") as f:
            f.write(content)
        return {"url": f"/uploads/{sub_dir}/{filename}", "filename": filename}

    return app


app = create_app()
