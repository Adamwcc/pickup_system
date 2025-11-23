# 檔案路徑: app/security.py
# 這是重構的第二步，提供了完整、標準的認證和授權功能。

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# 為了打破循環匯入，我們只在函式內部匯入需要的模組
from . import crud, schemas, models, database

# --- 1. 設定 ---
# 在真實部署中，應從環境變數讀取
SECRET_KEY = "a_very_secret_key_for_dev_should_be_changed"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# 這個 URL 指向 auth.py 中的登入 API
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# --- 2. 密碼處理工具 ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_content.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- 3. JWT Token 處理工具 ---
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- 4. FastAPI 依賴項 (Dependencies) ---
# 這些是我們注入到 API 端點中，用來保護路由和獲取當前使用者的核心函式。

def get_db():
    """ 獨立的 get_db 依賴項，方便在各處使用 """
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> models.User:
    """
    基礎依賴項：解碼 Token，從資料庫獲取使用者。
    如果 Token 無效或找不到使用者，會拋出 401 錯誤。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
        token_data = schemas.TokenData(phone_number=phone_number)
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_phone(db, phone_number=token_data.phone_number)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    通用依賴項：確保使用者是 'active' 狀態。
    適用於所有需要登入且帳號正常的普通操作。
    """
    if current_user.status != models.UserStatus.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user

def get_current_teacher_user(
    current_user: models.User = Depends(get_current_active_user)
) -> models.User:
    """
    權限依賴項：確保使用者是 'teacher' 或 'admin'。
    """
    if current_user.role not in [models.UserRole.teacher, models.UserRole.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Requires teacher or admin privileges."
        )
    return current_user

def get_current_admin_user(
    current_user: models.User = Depends(get_current_active_user)
) -> models.User:
    """
    最高權限依賴項：確保使用者是 'admin'。
    """
    if current_user.role != models.UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Requires admin privileges."
        )
    return current_user

