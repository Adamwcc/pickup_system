# 檔案路徑: app/main.py

from fastapi import FastAPI
from .database import engine, Base
from .routers import auth, users, admin # <--- 確保 admin 在這裡

# Base.metadata.create_all(bind=engine) # 我們現在使用 Alembic，不再需要這一行

app = FastAPI(
    title="校園接送系統 API",
    description="一個專業的、符合多租戶架構的安親班管理系統。",
    version="2.0.0" #<--- 版本升級！
)

# --- 包含核心路由 ---
app.include_router(auth.router, prefix="/api/v1/auth", tags=["1. 認證 (Authentication)"])
app.include_router(users.router, prefix="/api/v1/users", tags=["2. 使用者 (Users)"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["3. 機構管理 (Admin)"]) # <--- 取消註解這一行

# --- 將所有其他非核心的路由保持註解 ---
# app.include_router(teachers.router, prefix="/api/v1/teachers", tags=["Teacher Actions"])
# app.include_router(pickups.router, prefix="/api/v1/pickups", tags=["Pickup Process"])
# app.include_router(websockets.router, prefix="/api/v1/ws", tags=["WebSocket"])
# app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "校園接送系統 API v2.0 - 奠基完成，機構管理功能已上線"} 

@app.get("/health", tags=["Root"])
def health_check():
    return {"status": "ok"}
