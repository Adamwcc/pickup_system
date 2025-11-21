# 檔案路徑: pickup_system/app/routers/websockets.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from typing import Dict, List

from .. import models
from ..dependencies import get_current_user_from_token # 我們下一步會建立它

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.room_connections: Dict[str, List[WebSocket]] = {}
        self.user_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: int):
        await websocket.accept()
        if room_id not in self.room_connections: self.room_connections[room_id] = []
        self.room_connections[room_id].append(websocket)
        if user_id not in self.user_connections: self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str, user_id: int):
        if room_id in self.room_connections and websocket in self.room_connections[room_id]:
            self.room_connections[room_id].remove(websocket)
        if user_id in self.user_connections and websocket in self.user_connections[user_id]:
            self.user_connections[user_id].remove(websocket)

    async def broadcast_to_room(self, message: dict, room_id: str):
        if room_id in self.room_connections:
            for connection in self.room_connections[room_id]:
                await connection.send_json(message)

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.user_connections:
            for connection in self.user_connections[user_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@router.websocket("/{notification_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    notification_id: str,
    current_user: models.User = Depends(get_current_user_from_token)
):
    if current_user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, room_id=notification_id, user_id=current_user.id)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast_to_room(data, room_id=notification_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id=notification_id, user_id=current_user.id)
