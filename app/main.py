# 檔案路徑: app/main.py

from fastapi import FastAPI
from .database import engine, Base

# --- 1. 只匯入我們需要的、已經重構過的核心路由 ---
from .routers import auth, users 
# from .routers import auth, admin, pickups, websockets, users, teachers, dashboard # <--- 刪除或註解掉這一整行舊的 import

# 應用程式啟動時，自動建立資料庫檔案和資料表
# 注意：在生產環境中，我們更依賴 Alembic，所以這行可以考慮移除，但暫時保留也無妨。
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="校園接送系統 API - 核心穩定版",
    description="這是一個由 Manus AI 協助重構的專案。目前處於第一階段，只啟用核心的認證與使用者模組。",
    version="2.0.0-core"
)

# --- 2. 只包含核心路由 ---
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])

# --- 確認所有非核心的路由都已被註解掉 ---
# app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin Management"])
# app.include_router(teachers.router, prefix="/api/v1/teachers", tags=["Teacher Actions"])
# app.include_router(pickups.router, prefix="/api/v1/pickups", tags=["Pickup Process"])
# app.include_router(websockets.router, prefix="/api/v1/ws", tags=["WebSocket"])
# app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])


@app.get("/")
def read_root():
    # 我們加入一個獨一無二的版本號來進行追蹤
    return {"message": "SYNC-TEST-VERSION-FOUR-SUCCESS"} 

@app.get("/health")
def health_check():
    return {"status": "ok"}
