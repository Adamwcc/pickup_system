from fastapi import FastAPI
from . import models
from .database import engine
from .routers import auth

# 在應用程式啟動時，根據 models.py 中的定義，在資料庫中建立所有表格
models.Base.metadata.create_all(bind=engine)

# 建立一個 FastAPI 應用程式實例
app = FastAPI(
    title="補習班接送系統 API",
    description="這是一個用於補習班接送通知系統的後端 API。",
    version="0.2.0", # 版本升級
)

# 引入新的 API 路由
app.include_router(auth.router)

# --- API 端點 (API Endpoints) ---

@app.get("/", tags=["系統狀態 (System Status)"])
def read_root():
    """
    根目錄端點，用於檢查 API 是否成功運行。
    訪問時會回傳一個歡迎訊息。
    """
    return {"message": "補習班接送系統 API 已成功運行！版本 0.2.0"}

@app.get("/health", tags=["系統狀態 (System Status)"])
def health_check():
    """
    健康檢查端點，提供更詳細的服務狀態。
    許多雲端平台會使用這個端點來監控應用程式是否正常。
    """
    return {"status": "ok", "service": "Pickup System API"}
