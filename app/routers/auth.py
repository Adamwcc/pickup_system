# 位於 app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta # <--- 修改這一行


from .. import crud, schemas, security, models, database
from ..dependencies import get_db

# 從設定檔讀取密鑰和過期時間
ACCESS_TOKEN_EXPIRE_MINUTES = security.ACCESS_TOKEN_EXPIRE_MINUTES
SECRET_KEY = security.SECRET_KEY
ALGORITHM = security.ALGORITHM

router = APIRouter()

# --- 驗證函式 (它的家就在這裡！) ---
def authenticate_user(db: Session, phone_number: str, password: str):
    """
    驗證使用者的手機號碼和密碼。
    返回使用者物件如果驗證成功，否則返回 None。
    """
    user = crud.get_user_by_phone(db, phone_number=phone_number)
    if not user:
        return None # 找不到使用者
    
    # 如果使用者是 invited 狀態，他還沒有密碼
    if not user.hashed_password:
        return None

    if not security.verify_password(password, user.hashed_password):
        return None # 密碼不正確
        
    return user


# --- 全新的「啟用帳號」API ---
@router.post("/activate", response_model=schemas.UserOut, summary="啟用家長帳號")
def activate_user_account(
    form_data: schemas.UserActivate, 
    db: Session = Depends(get_db)
):
    """
    家長首次使用時，透過此 API 啟用帳號。
    1. 驗證機構代碼和學生姓名是否匹配。
    2. 驗證該手機號對應的使用者是否為 'invited' 狀態。
    3. 設定密碼並將使用者狀態更新為 'active'。
    """
    # 1. 驗證家長是否有權限認領這個學生
    student = crud.claim_student(
        db=db,
        parent_phone=form_data.phone_number,
        institution_code=form_data.institution_code,
        student_name=form_data.student_full_name
    )
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="啟用失敗：找不到對應的機構代碼或學生姓名，或您的手機號與預留號碼不符",
        )

    # 2. 獲取使用者並檢查狀態
    user = crud.get_user_by_phone(db, phone_number=form_data.phone_number)
    if not user or user.status != models.UserStatus.invited:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此帳號無法被啟用，可能已啟用或不存在",
        )

    # 3. 啟用帳號
    return crud.activate_parent_account(db=db, user=user, password=form_data.password)


# --- 修改後的「登入」API ---
@router.post("/token", response_model=schemas.Token, summary="使用者登入")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    使用者（家長、老師、管理員）登入以獲取 Access Token。
    """
    user = authenticate_user(db, form_data.username, form_data.password) # <--- 在這裡被呼叫
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手機號碼或密碼不正確",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 登入時，不允許 'invited' 或 'inactive' 狀態的使用者獲取 token
    if user.status != models.UserStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"帳號狀態異常 ({user.status.value})，無法登入",
        )

     # 1. 計算過期時間
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 2. 準備要編碼的資料，將過期時間 'exp' 也放進去
    to_encode = {
        "sub": user.phone_number,
        "exp": expire
    }
    
    # 3. 呼叫 create_access_token，只傳遞 data 參數
    access_token = security.create_access_token(data=to_encode)
    
    return {"access_token": access_token, "token_type": "bearer"}
