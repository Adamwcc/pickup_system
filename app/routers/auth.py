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


@router.post("/activate", response_model=schemas.UserOut, summary="家長啟用帳號並綁定第一位學生")
def activate_parent_account_and_claim_student(
    activation_data: schemas.ParentActivate, # <--- 使用新的 Schema
    db: Session = Depends(get_db)
):
    """
    家長首次啟用帳號的流程，嚴格遵循'憲法'的雙重驗證。
    1. 驗證機構代碼是否存在。
    2. 驗證手機號是否為 'invited' 狀態。
    3. 驗證該機構下是否有對應姓名的學生。
    4. 如果全部通過，則啟用帳號、設定密碼，並建立綁定關係。
    """
    # 1. 驗證機構
    institution = crud.get_institution_by_code(db, code=activation_data.institution_code)
    if not institution:
        raise HTTPException(status_code=404, detail="機構代碼不正確")

    # 2. 驗證使用者
    user = crud.get_user_by_phone(db, phone_number=activation_data.phone_number)
    if not user or user.status != models.UserStatus.invited:
        raise HTTPException(status_code=403, detail="此手機號碼未被邀請或帳號已啟用")

    # 3. 驗證學生
    student = crud.get_student_by_name_and_institution(
        db, 
        student_name=activation_data.student_name, 
        institution_id=institution.id
    )
    if not student:
        raise HTTPException(status_code=404, detail="在此機構下找不到該姓名的學生")

    # 4. 執行啟用和綁定
    activated_user = crud.activate_parent_account(db, user=user, password=activation_data.password)
    crud.link_parent_to_student(db, parent_id=activated_user.id, student_id=student.id)
    
    # 將家長與機構關聯
    activated_user.institution_id = institution.id
    db.commit()
    db.refresh(activated_user)

    return activated_user
