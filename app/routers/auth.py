from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import SessionLocal

# 建立 API 路由
router = APIRouter(
    prefix="/users",
    tags=["Users & Authentication"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    使用者註冊 API。
    - 檢查手機號碼是否已被註冊。
    - 創建新使用者並將密碼加密儲存。
    """
    db_user = crud.get_user_by_phone(db, phone_number=user.phone_number)
    if db_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    # 預設新註冊的家長角色為 'parent'
    if user.role not in ["parent", "teacher", "admin"]:
        user.role = "parent"
        
    return crud.create_user(db=db, user=user)

# 待辦：
# 1. 登入 API (/token)
# 2. 簡訊驗證 API
