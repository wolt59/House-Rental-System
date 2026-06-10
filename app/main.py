import logging
from contextlib import asynccontextmanager
import os
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException, status, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.api_v1.api import api_router
from app.api.deps import get_current_active_user
from app.api.websocket import ws_manager
from app.cache.redis_client import close_redis, is_redis_available
from app.core.config import settings
from app.core.security import decode_access_token
from app.crud import crud_user
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.user import User

logger = logging.getLogger("hrs")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
# 聊天上传子目录列表，目录创建延后到 lifespan 启动事件中执行，
# 以避免在生产环境对应用目录无写权限时直接抛出 PermissionError 阻断应用启动。
UPLOAD_SUBDIRS = ("images", "audios", "videos", "files")

# 聊天上传白名单
CHAT_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp", "image/svg+xml"}
CHAT_AUDIO_TYPES = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/x-m4a", "audio/aac", "audio/webm"}
CHAT_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
# 常见文档类型
CHAT_DOCUMENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "text/csv",
    "text/markdown",
    "application/zip",
    "application/x-rar-compressed",
    "application/x-7z-compressed",
    "application/json",
}
CHAT_MAX_SIZE = 20 * 1024 * 1024  # 聊天文件上限 20MB
LEGACY_MAX_SIZE = 10 * 1024 * 1024  # 兼容老接口 10MB


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：确保上传目录存在
    # 必须在请求处理之前完成；如果权限不足，仅记录告警，让应用继续启动
    # （管理员可在挂载好外部卷后通过运维手段恢复；chat 上传接口会按需报错）
    for sub in UPLOAD_SUBDIRS:
        target = os.path.join(UPLOAD_DIR, sub)
        try:
            os.makedirs(target, exist_ok=True)
        except OSError as e:
            logger.warning(
                "Failed to create upload subdirectory %s (errno=%s): %s. "
                "Chat uploads may fail until the directory is created with proper permissions.",
                target, e.errno, e,
            )

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

    # check_dir=False：避免在 create_app() 阶段因目录尚不存在而抛出 RuntimeError；
    # 目录创建由 lifespan 启动事件负责；请求到来时目录通常已就绪。
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR, check_dir=False), name="uploads")

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
        if len(content) > LEGACY_MAX_SIZE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 10MB)")
        with open(file_path, "wb") as f:
            f.write(content)
        return {"url": f"/uploads/{sub_dir}/{filename}", "filename": filename}

    @app.post("/api/v1/upload/chat", tags=["upload"])
    async def upload_chat_file(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_active_user),
    ):
        """聊天消息专用上传接口：支持图片/音频/视频/文件，并返回类型、大小等元数据。"""
        content_type = (file.content_type or "").lower()
        if content_type in CHAT_IMAGE_TYPES:
            sub_dir = "images"
            message_type = "image"
        elif content_type in CHAT_AUDIO_TYPES:
            sub_dir = "audios"
            message_type = "audio"
        elif content_type in CHAT_VIDEO_TYPES:
            sub_dir = "videos"
            message_type = "video"
        elif content_type in CHAT_DOCUMENT_TYPES:
            sub_dir = "files"
            message_type = "file"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {content_type}",
            )

        original_name = file.filename or "file"
        ext = os.path.splitext(original_name)[1]
        # 移除路径分隔符等不安全字符，限制扩展名长度
        safe_ext = "".join(ch for ch in ext if ch.isalnum() or ch == ".")[:10]
        stored_name = f"{uuid.uuid4().hex}{safe_ext}"
        sub_path = os.path.join(UPLOAD_DIR, sub_dir)
        file_path = os.path.join(sub_path, stored_name)
        content = await file.read()
        size = len(content)
        if size == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
        if size > CHAT_MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large (max {CHAT_MAX_SIZE // (1024 * 1024)}MB)",
            )
        # 兜底创建子目录：lifespan 中已尽力创建；若启动时权限受限导致目录缺失，
        # 在请求阶段再尝试一次，错误信息更直观
        try:
            os.makedirs(sub_path, exist_ok=True)
        except OSError as e:
            logger.error("Cannot create upload subdirectory %s: %s", sub_path, e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Upload directory is not writable on the server",
            )
        with open(file_path, "wb") as f:
            f.write(content)
        return {
            "url": f"/uploads/{sub_dir}/{stored_name}",
            "filename": stored_name,
            "original_name": original_name,
            "size": size,
            "mime_type": content_type,
            "message_type": message_type,
        }

    return app


app = create_app()
