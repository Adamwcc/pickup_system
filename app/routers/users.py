# 檔案路徑: app/routers/users.py
# 版本：v2.2 - 為 API 端點添加中文摘要

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas, security
from ..dependencies import get_db

router = APIRouter(
    responses={404: {"description": "Not found"}},
)

@router.get("/me", response_model=schemas.UserDetail, summary="獲取個人完整資訊")
def read_users_me(
    current_user: models.User = Depends(security.get_current_active_user)
):
    """獲取當前登入使用者的完整資訊，包括其關聯的子女列表。"""
    return current_user


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT, summary="修改個人密碼")
def update_my_password(
    password_data: schemas.UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """使用者提供舊密碼以驗證身份，並更新為新密碼。"""
    if not security.verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="舊密碼不正確")
    
    crud.update_user_password(db, user=current_user, new_password=password_data.new_password)
    return


@router.post("/me/children", response_model=schemas.UserDetail, summary="【家長】手動綁定子女")
def bind_additional_child(
    binding_data: schemas.ChildBindingCreate,
    db: Session = Depends(get_db),
    current_parent: models.User = Depends(security.get_current_active_parent)
):
    """【家長】為自己綁定一個額外的子女（例如，老師新增時遺漏或輸錯號碼的情況）。"""
    updated_user = crud.bind_child_to_parent(
        db=db, 
        parent=current_parent, 
        child_info=binding_data
    )
    return updated_user


@router.delete("/me/children/{student_id}", status_code=status.HTTP_204_NO_CONTENT, summary="【家長】解除子女綁定")
def unbind_my_child(
    student_id: int,
    db: Session = Depends(get_db),
    current_parent: models.User = Depends(security.get_current_active_parent)
):
    """【家長】從自己的帳號中，主動解除與某個子女的綁定關係。"""
    success = crud.unbind_student_from_parent_by_ids(
        db=db, 
        parent_id=current_parent.id, 
        student_id=student_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="找不到您與該學生的綁定關係")
    return
