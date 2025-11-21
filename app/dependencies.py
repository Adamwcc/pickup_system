# 檔案路徑: pickup_system/app/dependencies.py

from fastapi import Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from . import crud, models, security, database

# 建立一個 OAuth2 "流程" 的實例，它指向獲取 token 的 API 端點
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_db():
    """
    一個 FastAPI 的依賴項，用於為每個請求建立一個獨立的資料庫會話。
    """
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    """
    一個依賴項，用於從 Authorization header 中的 Bearer token 解析出當前使用者。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="無法驗證憑證",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_phone(db, phone_number=phone_number)
    if user is None:
        raise credentials_exception
    return user

def get_current_admin_user(
    current_user: models.User = Depends(get_current_user)
):
    """
    一個依賴項，用於確保當前使用者是管理員 (admin)。
    """
    if current_user.role != models.UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="權限不足，需要管理員權限"
        )
    return current_user

def get_current_teacher_user(
    current_user: models.User = Depends(get_current_user)
):
    """
    一個依賴項，用於確保當前使用者至少是老師 (teacher) 或更高權限。
    """
    allowed_roles = [models.UserRole.teacher, models.UserRole.admin]
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足，需要教師或管理員權限"
        )
    return current_user

async def get_current_user_from_token(
    token: str = Query(...), 
    db: Session = Depends(get_db)
):
    """一個專門給 WebSocket 用的依賴項，從查詢參數中獲取 token 並驗證使用者。"""
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            return None
    except JWTError:
        return None
    
    user = crud.get_user_by_phone(db, phone_number=phone_number)
    return user

