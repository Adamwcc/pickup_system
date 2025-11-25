# 檔案路徑: app/routers/users.py
# 版本：v2.1 - 重構為統一使用 security 模組的權限依賴項

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas, security
from ..dependencies import get_db

# vvv--- 這是我們要修改的地方 ---vvv
# 移除 router 層級的通用依賴，改為在每個 API 內部精確定義
router = APIRouter(
    responses={404: {"description": "Not found"}},
)
# ^^^--- 修改結束 ---^^^


@router.get("/me", response_model=schemas.UserDetail)
def read_users_me(
    # 【修正】: 任何 active 使用者都能看自己的資訊
    current_user: models.User = Depends(security.get_current_active_user)
):
    """獲取當前登入使用者的完整資訊。"""
    return current_user


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def update_my_password(
    password_data: schemas.UserPasswordUpdate,
    db: Session = Depends(get_db),
    # 【修正】: 任何 active 使用者都能改自己的密碼
    current_user: models.User = Depends(security.get_current_active_user)
):
    """使用者修改自己的登入密碼。"""
    if not security.verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="舊密碼不正確")
    
    crud.update_user_password(db, user=current_user, new_password=password_data.new_password)
    return


@router.post("/me/children", response_model=schemas.UserDetail)
def bind_additional_child(
    binding_data: schemas.ChildBindingCreate,
    db: Session = Depends(get_db),
    # 【修正】: 明確此操作需要家長身份
    current_parent: models.User = Depends(security.get_current_active_parent)
):
    """【家長】為自己綁定一個額外的子女。"""
    updated_user = crud.bind_child_to_parent(
        db=db, 
        parent=current_parent, 
        child_info=binding_data
    )
    return updated_user


@router.delete("/me/children/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def unbind_my_child(
    student_id: int,
    db: Session = Depends(get_db),
    # 【修正】: 統一變數名，並確認依賴項正確
    current_parent: models.User = Depends(security.get_current_active_parent)
):
    """【家長】主動解除與某個子女的綁定。"""
    success = crud.unbind_student_from_parent_by_ids(
        db=db, 
        parent_id=current_parent.id, 
        student_id=student_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="找不到您與該學生的綁定關係")
    return
