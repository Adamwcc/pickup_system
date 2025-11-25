# 檔案路徑: app/routers/admin.py
# 版本：基於新憲法的 v2.0
# 說明：實現了機構管理員的核心 API。

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas, security
from ..dependencies import get_db

router = APIRouter()

# --- 權限依賴項 ---
def get_current_admin_user(current_user: models.User = Depends(security.get_current_active_user)):
    """
    一個依賴項，用於驗證當前使用者是否為 'admin'。
    """
    if current_user.role != models.UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足：此操作需要機構管理員權限。"
        )
    if not current_user.institution_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="操作失敗：您的管理員帳號未歸屬任何機構。"
        )
    return current_user

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
    current_admin: models.User = Depends(get_current_admin_user)
):
    """
    由已登入的機構管理員，在自己所屬的機構下，建立一位新的教職員。

    - **權限**: `admin`
    - **角色**: 可建立 `teacher`, `receptionist`, `admin` 等角色。
    """
    # 檢查手機號是否已被註冊
    if crud.get_user_by_phone(db, phone_number=staff_data.phone_number):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="該手機號碼已被註冊，請使用其他號碼。"
        )
    
    # 檢查角色是否合法
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
    current_admin: models.User = Depends(get_current_admin_user)
):
    """
    由已登入的機構管理員，在自己所屬的機構下，建立一個新的班級。

    - **權限**: `admin`
    - **注意**: 如果提供了 `teacher_id`，系統不會自動驗證該老師是否存在或屬於同機構，
      這部分驗證邏輯可以在未來加入或由前端輔助。
    """
    return crud.create_class(
        db=db, 
        class_data=class_data, 
        institution_id=current_admin.institution_id
    )

# 刪除使用者(Delete User)

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(security.get_current_active_admin) # 假設您有這個依賴項
):
    """【管理員】刪除任何使用者（家長、老師、其他管理員）。"""
    # 增加一個保護，防止管理員刪除自己
    if current_admin.id == user_id:
        raise HTTPException(status_code=400, detail="管理員不能刪除自己")

    deleted_user = crud.delete_user_by_id(db=db, user_id=user_id)
    
    if not deleted_user:
        raise HTTPException(status_code=404, detail="找不到指定的使用者")
    return


# 注意：我們暫時移除了「建立機構」的 API。
# 因為在多租戶系統中，「建立機構」通常由超級管理員完成，
# 或者透過一個獨立的、更複雜的註冊流程來完成。
# 我們可以稍後再把它加回來。
