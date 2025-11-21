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
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin Management"])
# 在下面新增 teachers.router 這一行
app.include_router(teachers.router, prefix="/api/v1/teachers", tags=["Teacher Actions"])
app.include_router(pickups.router, prefix="/api/v1/pickups", tags=["Pickup Process"])
app.include_router(websockets.router, prefix="/api/v1/ws", tags=["WebSocket"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])

@app.get("/")
def read_root():
    return {"message": "補習班接送系統 API 已成功運行！版本 1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
