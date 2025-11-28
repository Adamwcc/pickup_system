# 檔案路徑: app/main.py (v2.1 - 錯誤處理增強版)

# --- 導入 ---
from app.core import logging_config

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse # <--- 新的導入

from .database import engine, Base
from .routers import auth, users, admin, teachers

# vvv --- 【新的導入】 --- vvv
from .core.logging_config import get_logger
# ^^^ --- 【新的導入】 --- ^^^

# vvv --- 【初始化 logger】 --- vvv
logger = get_logger(__name__)
# ^^^ --- 【初始化 logger】 --- ^^^

app = FastAPI(
    title="校園接送系統 API",
    description="一個專業的、符合多租戶架構的安親班管理系統。",
    version="2.0.0"
)

# vvv --- 【添加全域異常處理中介軟體】 --- vvv
@app.middleware("http" )
async def global_exception_handler(request: Request, call_next):
    """
    全域異常捕獲中介軟體。
    用於捕獲所有未被處理的異常，記錄 500 錯誤，並返回一個標準的 JSON 響應。
    """
    try:
        # 將請求傳遞給後續的處理程序 (API 路由)
        response = await call_next(request)
        return response
    except Exception as e:
        # 捕獲到了未被處理的異常！
        # 這是一個 500 Internal Server Error
        
        # 使用 logger.error 記錄完整的錯誤資訊和堆疊追蹤
        logger.error(
            f"發生未處理的伺服器內部錯誤 (500): {e}",
            exc_info=True # exc_info=True 會自動附加堆疊追蹤資訊
        )
        
        # 向客戶端返回一個標準的、安全的 500 錯誤響應
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )
# ^^^ --- 【添加全域異常處理中介軟體】 --- ^^^


# --- 包含核心路由 (保持不變) ---
app.include_router(auth.router, prefix="/api/v1/auth", tags=["1. 認證 (Authentication)"])
app.include_router(users.router, prefix="/api/v1/users", tags=["2. 使用者 (Users)"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["3. 機構管理 (Admin)"])
app.include_router(teachers.router, prefix="/api/v1/teachers", tags=["4. 教職員 (Teachers)"]) 

# --- 根端點 (保持不變) ---
@app.get("/", tags=["Root"])
def read_root():
    return {"message": "校園接送系統 API v2.0 - 奠基完成，機構管理功能已上線"} 

@app.get("/health", tags=["Root"])
def health_check():
    return {"status": "ok"}
