# 檔案路徑: app/security.py
# 版本：基於新憲法的 v2.0
# 說明：提供了完整的密碼處理、Token 生成和使用者認證功能。

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from . import crud, models, schemas
from .dependencies import get_db

# --- 環境變數與常數 ---
# 在真實部署中，這些值應從環境變數讀取
SECRET_KEY = "a_very_secret_key_for_dev_v2" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # Token 有效期 7 天

# --- 密碼處理 ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證純文字密碼與雜湊值是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """為純文字密碼生成雜湊值"""
    return pwd_context.hash(password)

# --- 使用者認證核心函式 ---
def authenticate_user(db: Session, phone_number: str, password: str) -> models.User | None:
    """
    使用者認證函式。
    1. 根據手機號找到使用者。
    2. 驗證密碼是否正確。
    3. 檢查帳號是否為 active 狀態。
    如果全部通過，返回 user 物件；否則返回 None。
    """
    user = crud.get_user_by_phone(db, phone_number=phone_number)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if user.status != models.UserStatus.active:
        return None # 可以針對 invited 或 inactive 狀態給出不同提示
    return user

# --- JWT Token 處理 ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    建立 JWT Access Token。
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- FastAPI 依賴項 ---
def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> models.User:
    """
    解析 Token，獲取當前使用者，但不檢查 active 狀態。
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
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    獲取當前已登入且狀態為 'active' 的使用者。
    這是在 API 端點中最常用的權限依賴項。
    """
    if current_user.status != models.UserStatus.active:
        raise HTTPException(status_code=400, detail="使用者帳號未啟用或已被停用")
    return current_user
