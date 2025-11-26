# 檔案路徑: app/routers/users.py
# 版本：v2.3 - 新增家長接送流程 API

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from .. import crud, models, schemas, security
from ..dependencies import get_db

router = APIRouter(
    # 將通用的權限依賴項放在這裡，確保此路由下的所有 API 都需要使用者登入
    dependencies=[Depends(security.get_current_active_user)],
    responses={404: {"description": "Not found"}},
    tags=["2. 使用者個人中心 (Users)"] # 統一在這裡設定 Tag
)

@router.get("/me", response_model=schemas.UserDetail, summary="獲取個人完整資訊")
def read_users_me(current_user: models.User = Depends(security.get_current_active_user)):
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
    """【家長】為自己綁定一個額外的子女。"""
    return crud.bind_child_to_parent(db=db, parent=current_parent, child_info=binding_data)

@router.delete("/me/children/{student_id}", status_code=status.HTTP_204_NO_CONTENT, summary="【家長】解除子女綁定")
def unbind_my_child(
    student_id: int,
    db: Session = Depends(get_db),
    current_parent: models.User = Depends(security.get_current_active_parent)
):
    """【家長】從自己的帳號中，主動解除與某個子女的綁定關係。"""
    success = crud.unbind_student_from_parent_by_ids(db=db, parent_id=current_parent.id, student_id=student_id)
    if not success:
        raise HTTPException(status_code=404, detail="找不到您與該學生的綁定關係")
    return

# vvv---接送發起API---vvv
@router.post(
    "/me/children/{student_id}/pickup", 
    response_model=schemas.StudentOut, 
    summary="【家長】發起接送"
)
def parent_starts_pickup(
    student_id: int,
    db: Session = Depends(get_db),
    current_parent: models.User = Depends(security.get_current_active_parent)
):
    """
    家長點擊「出發」按鈕時呼叫此 API。
    系統會將學生狀態更新為 '家長已出發'，並向機構端廣播通知。
    """
    student = crud.get_student_by_id(db, student_id=student_id)
    if not student:
        raise HTTPException(status_code=404, detail="找不到指定的學生")
    
    return crud.start_pickup_process(db=db, student=student, parent=current_parent)


# 我們需要一個新的 Pydantic 模型來接收 ETA
class EtaUpdate(BaseModel):
    minutes_remaining: int

@router.post(
    "/me/children/{student_id}/eta", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="【家長】更新預計到達時間 (ETA)"
)
def parent_updates_eta(
    student_id: int,
    eta_data: EtaUpdate,
    db: Session = Depends(get_db),
    current_parent: models.User = Depends(security.get_current_active_parent)
):
    """
    由家長端 App 在背景呼叫，用於向機構端廣播 ETA 更新。
    """
    student = crud.get_student_by_id(db, student_id=student_id)
    if not student:
        raise HTTPException(status_code=404, detail="找不到指定的學生")
        
    crud.update_pickup_eta(
        db=db, 
        student=student, 
        parent=current_parent, 
        minutes_remaining=eta_data.minutes_remaining
    )
    return

