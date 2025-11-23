from fastapi import FastAPI
from .database import engine, Base
# 在下面這一行中，加入 teachers
from .routers import auth, admin, pickups, websockets, users, teachers, dashboard

# 應用程式啟動時，自動建立資料庫檔案和資料表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="校園接送系統 API",
    description="這是一個由 Manus AI 協助開發的專案，現已升級至 v1.0，加入了精細化的班級管理與教師權限功能。",
    version="1.0.0" #<--- 版本升級！
)

# 包含各個模組的路由
# --- 2. 只包含核心路由 ---
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])

# --- 將所有非核心的路由都註解掉 ---
# app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin Management"])
# app.include_router(teachers.router, prefix="/api/v1/teachers", tags=["Teacher Actions"])
# app.include_router(pickups.router, prefix="/api/v1/pickups", tags=["Pickup Process"])
# app.include_router(websockets.router, prefix="/api/v1/ws", tags=["WebSocket"])
# app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])


@app.get("/")
def read_root():
    # 我們加入一個獨一無二的版本號來進行追蹤
    return {"message": "SYNC-TEST-V3-SUCCESS"} 

@app.get("/health")
def health_check():
    return {"status": "ok"}
