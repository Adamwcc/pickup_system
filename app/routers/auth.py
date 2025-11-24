# 檔案路徑: app/routers/auth.py
# 版本：基於新憲法的 v2.0
# 說明：實現了標準化的登入和家長啟用流程。

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from .. import crud, models, schemas, security
from ..dependencies import get_db

router = APIRouter()

@router.post("/token", response_model=schemas.Token, summary="使用者登入獲取 Token")
def login_for_access_token(
    db: Session = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    標準的 OAuth2 密碼流登入。
    - 使用者提供 username (這裡用手機號) 和 password。
    - 成功後返回 access_token。
    """
    user = security.authenticate_user(db, phone_number=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手機號碼或密碼不正確",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.phone_number}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# vvv--- 家長首次綁定學生API ---vvv
@router.post("/activate-parent", response_model=schemas.UserOut, summary="家長啟用帳號")
def activate_parent(
    activation_data: schemas.ParentActivation,
    db: Session = Depends(get_db)
):
    """
    供家長首次使用時，啟用他們的 'invited' 帳號。

    家長需要提供他們的手機號、自訂的密碼，以及他們孩子的機構代碼和姓名，
    以驗證他們的身份。
    """
    activated_user = crud.activate_parent_account(db, activation_data=activation_data)
    
    if not activated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="啟用失敗：手機號碼、機構代碼或學生姓名不匹配，或帳號非待啟用狀態。",
        )
    
    return activated_user