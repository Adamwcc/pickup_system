from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..websocket import manager
import json

router = APIRouter()

@router.websocket("/ws/pickup/{notification_id}")
async def websocket_endpoint(websocket: WebSocket, notification_id: int):
    """
    處理接送通知的即時通訊。
    家長和老師都會連線到同一個以 notification_id 命名的房間。
    """
    room_name = f"notification_{notification_id}"
    await manager.connect(websocket, room_name)
    
    try:
        while True:
            # 等待從客戶端接收訊息 (例如，家長上傳的 GPS)
            data = await websocket.receive_text()
            
            # --- 模擬 ETA 計算與廣播 ---
            # 在真實世界中，這裡會解析 GPS 數據，呼叫地圖服務
            # 現在，我們只做一個簡單的模擬
            
            # 假設家長端傳來的是 JSON 格式的 GPS 數據
            # 例如: {"lat": 25.0330, "lng": 121.5654}
            # 我們在這裡不做解析，只模擬計算出新的 ETA
            new_eta_minutes = 10 # 這裡可以改成 random.randint(5, 15) 來讓它更有趣
            
            # 準備要廣播給房間內所有人的訊息
            broadcast_message = {
                "event": "ETA_UPDATE",
                "notification_id": notification_id,
                "eta_minutes": new_eta_minutes
            }
            
            # 將訊息廣播給房間裡的所有人 (包括發送者自己)
            await manager.broadcast_to_room(json.dumps(broadcast_message), room_name)

    except WebSocketDisconnect:
        # 當客戶端斷開連線時，執行清理工作
        manager.disconnect(websocket, room_name)
        # 可以在這裡廣播一條「家長已離線」的訊息
        disconnect_message = {
            "event": "USER_DISCONNECTED",
            "message": "A user has left the channel."
        }
        await manager.broadcast_to_room(json.dumps(disconnect_message), room_name)
