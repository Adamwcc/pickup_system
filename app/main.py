from fastapi import FastAPI
from .database import engine, Base
from .routers import auth, admin, pickups, websockets # <--- 匯入 websockets

# 應用程式啟動時，自動建立資料庫檔案和資料表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="校園接送系統 API",
    description="這是一個由 Manus AI 協助開發的專案，現已加入 WebSocket 即時通訊功能。",
    version="0.6.0"
)

# 包含各個模組的路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin Management"])
app.include_router(pickups.router, prefix="/api/v1/pickups", tags=["Pickup Process"])
app.include_router(websockets.router, prefix="/api/v1", tags=["Real-time"]) # <--- 新增這一行

@app.get("/")
def read_root():
    return {"message": "補習班接送系統 API 已成功運行！版本 0.6.0"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
