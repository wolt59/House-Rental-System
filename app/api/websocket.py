import json
import logging
from typing import Dict, Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("websocket")


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected: user_id={user_id}, total_connections={len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected: user_id={user_id}")

    async def send_personal(self, message: dict, user_id: int):
        if user_id not in self.active_connections:
            return
        stale = set()
        for ws in self.active_connections[user_id]:
            try:
                await ws.send_text(json.dumps(message, ensure_ascii=False, default=str))
            except WebSocketDisconnect:
                stale.add(ws)
        for ws in stale:
            self.active_connections[user_id].discard(ws)
        if user_id in self.active_connections and not self.active_connections[user_id]:
            del self.active_connections[user_id]

    def is_online(self, user_id: int) -> bool:
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0


ws_manager = ConnectionManager()