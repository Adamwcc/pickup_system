from fastapi import FastAPI

# 建立一個 FastAPI 應用程式實例
app = FastAPI(
    title="補習班接送系統 API",
    description="這是一個用於補習班接送通知系統的後端 API。",
    version="0.1.0",
)

# --- API 端點 (API Endpoints) ---

@app.get("/", tags=["系統狀態 (System Status)"])
def read_root():
    """
    根目錄端點，用於檢查 API 是否成功運行。
    訪問時會回傳一個歡迎訊息。
    """
    return {"message": "補習班接送系統 API 已成功運行！版本 0.1.0"}

@app.get("/health", tags=["系統狀態 (System Status)"])
def health_check():
    """
    健康檢查端點，提供更詳細的服務狀態。
    許多雲端平台會使用這個端點來監控應用程式是否正常。
    """
    return {"status": "ok", "service": "Pickup System API"}

# --- 未來功能的預留位置 ---
# 我們之後會在這裡加入更多來自不同檔案的 API 路由 (Routers)
# 例如：app.include_router(auth.router)
# 例如：app.include_router(notifications.router)

