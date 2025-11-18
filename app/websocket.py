from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        # 使用一個字典來管理房間，鍵是房間名，值是連線列表
        # 例如: {"notification_1": [websocket1, websocket2]}
        self.rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_name: str):
        """處理一個新的連線，並將其加入指定房間。"""
        await websocket.accept()
        if room_name not in self.rooms:
            self.rooms[room_name] = []
        self.rooms[room_name].append(websocket)

    def disconnect(self, websocket: WebSocket, room_name: str):
        """處理一個斷開的連線，並將其從房間中移除。"""
        if room_name in self.rooms:
            self.rooms[room_name].remove(websocket)
            # 如果房間空了，可以選擇性地刪除房間
            if not self.rooms[room_name]:
                del self.rooms[room_name]

    async def broadcast_to_room(self, message: str, room_name: str):
        """向指定房間內的所有連線廣播一條訊息。"""
        if room_name in self.rooms:
            for connection in self.rooms[room_name]:
                await connection.send_text(message)

# 建立一個全域的 ConnectionManager 實例，供整個應用程式使用
manager = ConnectionManager()
