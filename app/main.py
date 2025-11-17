from fastapi import FastAPI
from .database import engine, Base
from .routers import auth, admin  # <--- 匯入 admin

# 應用程式啟動時，自動建立資料庫檔案和資料表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="校園接送系統 API",
    description="這是一個由 Manus AI 協助開發的專案，現已加入使用者認證與管理功能。",
    version="0.3.0"
)

# 包含認證功能的 API 路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
# 包含管理員功能的 API 路由
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin Management"]) # <--- 新增這一行

@app.get("/")
def read_root():
    return {"message": "補習班接送系統 API 已成功運行！版本 0.3.0"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
