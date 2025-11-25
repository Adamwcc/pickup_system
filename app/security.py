# 檔案路徑: app/security.py
# 版本：v2.1 - 修正了權限依賴項的遞歸錯誤

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from . import crud, models
from .dependencies import get_db

# --- 環境變數與常數 ---
SECRET_KEY = "a_very_secret_key_for_dev_v2" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

# --- 密碼處理 ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- 使用者認證核心函式 ---
def authenticate_user(db: Session, phone_number: str, password: str) -> models.User | None:
    user = crud.get_user_by_phone(db, phone_number=phone_number)
    if not user or not verify_password(password, user.hashed_password):
        return None
    # 我們只認證，不檢查 active，將 active 檢查交給依賴項
    return user

# --- JWT Token 處理 ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire_time = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire_time})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ===================================================================
# FastAPI 依賴項 (Dependencies) - 修正後的版本
# ===================================================================

def get_current_user_from_token(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> models.User:
    """
    【基礎依賴項】: 只負責從 Token 中解析出 User 物件。
    這是所有其他權限依賴項的基石。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="無法驗證憑證",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_phone(db, phone_number=phone_number)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(
    current_user: models.User = Depends(get_current_user_from_token),
) -> models.User:
    """
    【通用依賴項】: 獲取當前已登入且狀態為 'active' 的使用者。
    """
    if current_user.status != models.UserStatus.active:
        raise HTTPException(status_code=403, detail="使用者帳號未啟用或已被停用")
    return current_user

def get_current_active_admin(
    current_user: models.User = Depends(get_current_active_user),
) -> models.User:
    """【權限依賴項】: 驗證當前使用者是否為管理員 (admin)。"""
    if current_user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="權限不足，此操作需要管理員身份")
    return current_user

def get_current_active_teacher(
    current_user: models.User = Depends(get_current_active_user),
) -> models.User:
    """【權限依賴項】: 驗證當前使用者是否為老師 (teacher) 或管理員。"""
    if current_user.role not in [models.UserRole.teacher, models.UserRole.admin]:
        raise HTTPException(status_code=403, detail="權限不足，此操作需要教職員身份")
    return current_user

def get_current_active_parent(
    current_user: models.User = Depends(get_current_active_user),
) -> models.User:
    """【權限依賴項】: 驗證當前使用者是否為家長 (parent)。"""
    if current_user.role != models.UserRole.parent:
        raise HTTPException(status_code=403, detail="權限不足，此操作需要家長身份")
    return current_user
