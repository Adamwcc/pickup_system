# 檔案路徑: app/routers/admin.py
# 版本：v2.1 - 重構為統一使用 security 模組的權限依賴項

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas, security
from ..dependencies import get_db

# vvv--- 這是我們要修改的地方 ---vvv
# 移除本地的 get_current_admin_user 函式，因為它的功能已由 security.py 提供

router = APIRouter()
# ^^^--- 修改結束 ---^^^


# --- API 端點 ---

@router.post(
    "/staff/", 
    response_model=schemas.UserOut, 
    status_code=status.HTTP_201_CREATED,
    summary="管理員新增教職員"
)
def create_staff(
    staff_data: schemas.StaffCreate,
    db: Session = Depends(get_db),
    # 【修正】: 直接使用 security 模組中權威的依賴項
    current_admin: models.User = Depends(security.get_current_active_admin)
):
    """
    由已登入的機構管理員，在自己所屬的機構下，建立一位新的教職員。
    """
    # 【新增】: 可以在這裡加入對 institution_id 的檢查，雖然 get_current_active_admin 也可以做
    if not current_admin.institution_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="操作失敗：您的管理員帳號未歸屬任何機構。"
        )

    if crud.get_user_by_phone(db, phone_number=staff_data.phone_number):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="該手機號碼已被註冊，請使用其他號碼。"
        )
    
    allowed_roles = [models.UserRole.teacher, models.UserRole.receptionist, models.UserRole.admin]
    if staff_data.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"無法建立此角色。允許的角色為: {', '.join(r.value for r in allowed_roles)}"
        )

    return crud.create_staff_user(
        db=db, 
        staff_data=staff_data, 
        institution_id=current_admin.institution_id
    )

@router.post(
    "/classes/", 
    response_model=schemas.ClassOut, 
    status_code=status.HTTP_201_CREATED,
    summary="管理員新增班級"
)
def create_class_in_institution(
    class_data: schemas.ClassCreate,
    db: Session = Depends(get_db),
    # 【修正】: 直接使用 security 模組中權威的依賴項
    current_admin: models.User = Depends(security.get_current_active_admin)
):
    """
    由已登入的機構管理員，在自己所屬的機構下，建立一個新的班級。
    """
    if not current_admin.institution_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="操作失敗：您的管理員帳號未歸屬任何機構。"
        )

    return crud.create_class(
        db=db, 
        class_data=class_data, 
        institution_id=current_admin.institution_id
    )

@router.delete("/users/{user_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="管理員職權:刪除使用者帳號")
def delete_user_by_admin(
    user_id: int,
    db: Session = Depends(get_db),
    # 【確認】: 這裡的用法是正確的
    current_admin: models.User = Depends(security.get_current_active_admin)
):
    """【管理員】刪除任何使用者（家長、老師、其他管理員）。"""
    if current_admin.id == user_id:
        raise HTTPException(status_code=400, detail="管理員不能刪除自己")

    deleted_user = crud.delete_user_by_id(db=db, user_id=user_id)
    
    if not deleted_user:
        raise HTTPException(status_code=404, detail="找不到指定的使用者")
    return
