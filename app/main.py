import logging
from contextlib import asynccontextmanager
import os
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.api_v1.api import api_router
from app.api.websocket import ws_manager
from app.cache.redis_client import close_redis, is_redis_available
from app.core.config import settings
from app.core.security import decode_access_token
from app.crud import crud_user
from app.db.base import Base
from app.db.session import engine, SessionLocal

logger = logging.getLogger("hrs")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(os.path.join(UPLOAD_DIR, "images"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "videos"), exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：初始化数据库
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

    # 启动时：检查 Redis 连接
    if settings.CACHE_ENABLED:
        if is_redis_available():
            logger.info("Redis 缓存已启用: %s", settings.REDIS_URL)
        else:
            logger.warning("Redis 连接失败，缓存功能已自动降级，应用仍可正常运行")

    yield

    # 关闭时：释放 Redis 连接池
    close_redis()


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

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001, reason="Missing token")
            return
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if not user_id:
                await websocket.close(code=4001, reason="Invalid token")
                return
        except Exception:
            await websocket.close(code=4001, reason="Invalid token")
            return

        db = SessionLocal()
        try:
            user = crud_user.get_user(db, int(user_id))
            if not user or not user.is_active:
                await websocket.close(code=4001, reason="User inactive or not found")
                return
        finally:
            db.close()

        await ws_manager.connect(websocket, int(user_id))
        try:
            while True:
                data = await websocket.receive_text()
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket, int(user_id))
        except Exception:
            ws_manager.disconnect(websocket, int(user_id))

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
