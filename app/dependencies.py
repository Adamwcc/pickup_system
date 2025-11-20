from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from . import crud, models, security
from .database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(security.oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """
    解析 JWT token，獲取當前使用者。
    """
    from jose import JWTError
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="無法驗證憑證",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = crud.get_user_by_phone(db, phone_number=phone_number)
    if user is None:
        raise credentials_exception
    return user

def get_current_admin_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    一個依賴項，用來確保目前使用者是 admin。
    如果不是，就拋出 403 Forbidden 錯誤。
    """
    if current_user.role != models.UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足，需要管理員權限"
        )
    return current_user

def get_current_teacher_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    一個依賴項，用於驗證當前使用者是否為老師或管理員。
    
    這個函式會被注入到需要「老師」權限的 API 端點中。
    它首先會呼叫 get_current_user 來確保使用者已登入。
    然後，它會檢查該使用者的角色。
    
    我們在這裡也允許 'admin' 角色通過，因為在我們的系統設計中，
    管理員應該擁有老師的所有權限，這被稱為「權限繼承」。
    """
    if current_user.role not in [models.UserRole.teacher, models.UserRole.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足，需要老師或管理員身份"
        )
    return current_user