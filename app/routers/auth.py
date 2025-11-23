# 檔案路徑: app/routers/auth.py
# 這是重構的第四步，提供了標準的登入、啟用帳號等認證 API。

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import crud, schemas, security, models

router = APIRouter()

@router.post("/token", response_model=schemas.Token, summary="使用者登入獲取 Token")
def login_for_access_token(
    db: Session = Depends(security.get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    標準的 OAuth2 密碼流登入。
    使用者提供 username (這裡用手機號) 和 password。
    """
    user = crud.get_user_by_phone(db, phone_number=form_data.username)
    if not user or not user.hashed_password or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status != models.UserStatus.active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token = security.create_access_token(data={"sub": user.phone_number})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/activate", response_model=schemas.UserOut, summary="啟用被邀請的家長帳號")
def activate_invited_user(
    activation_data: schemas.UserActivation,
    db: Session = Depends(security.get_db)
):
    """
    被老師邀請的家長，透過此 API 設定密碼來啟用自己的帳號。
    """
    user = crud.get_user_by_phone(db, phone_number=activation_data.phone_number)
    if not user:
        raise HTTPException(status_code=404, detail="User with this phone number not found.")
    if user.status != models.UserStatus.invited:
        raise HTTPException(status_code=400, detail="User account is not in 'invited' status.")
        
    return crud.activate_user_account(db=db, user=user, password=activation_data.password)
