from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from typing import Dict, List

from .. import models
from ..dependencies import get_current_user_from_token # <--- 匯入真實的依賴項

router = APIRouter()

# ConnectionManager 類別的程式碼和上面第二步中的一樣，保持不變
class ConnectionManager:
    def __init__(self):
        self.room_connections: Dict[str, List[WebSocket]] = {}
        self.user_connections: Dict[int, List[WebSocket]] = {}
    # ... (connect, disconnect, broadcast_to_room, send_personal_message 方法)
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


@router.websocket("/ws/{notification_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    notification_id: str,
    # 這是關鍵：使用 Depends 將 HTTP 風格的依賴注入應用到 WebSocket
    current_user: models.User = Depends(get_current_user_from_token)
):
    # 如果 get_current_user_from_token 驗證失敗（回傳 None），FastAPI 會自動處理，
    # 但 WebSocket 需要我們手動處理連接關閉。
    if current_user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, room_id=notification_id, user_id=current_user.id)
    try:
        while True:
            data = await websocket.receive_json()
            # 可以在這裡增加更多處理客戶端訊息的邏輯
            # 例如，處理家長發來的 GPS 更新
            await manager.broadcast_to_room(data, room_id=notification_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id=notification_id, user_id=current_user.id)

