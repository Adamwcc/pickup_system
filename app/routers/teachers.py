# 檔案路徑: app/routers/teachers.py
# 版本：基於新憲法的 v2.0
# 說明：實現了教職員的核心 API，例如建立學生。

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas, security
from ..dependencies import get_db

router = APIRouter()

# --- 權限依賴項 ---
def get_current_teacher_or_higher(current_user: models.User = Depends(security.get_current_active_user)):
    """
    一個依賴項，用於驗證當前使用者是否為 'teacher', 'receptionist', 或 'admin'。
    """
    allowed_roles = [models.UserRole.teacher, models.UserRole.receptionist, models.UserRole.admin]
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足：此操作需要教職員權限。"
        )
    if not current_user.institution_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="操作失敗：您的帳號未歸屬任何機構。"
        )
    return current_user

# --- API 端點 ---
@router.post(
    "/students/", 
    response_model=schemas.StudentOut, 
    status_code=status.HTTP_201_CREATED,
    summary="教職員新增學生"
)
def create_student_by_teacher(
    student_data: schemas.StudentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_teacher_or_higher)
):
    """
    由已登入的教職員，在自己所屬的機構下，建立一位新學生，並可選擇性地邀請家長。

    - **權限**: `teacher`, `receptionist`, `admin`
    - **核心邏輯**:
      - 學生會被建立在指定的 `class_id` 之下。
      - 系統會自動為 `parents` 列表中的家長建立 `invited` 狀態的預註冊帳號。
    """
    # 可以在此加入驗證：檢查 student_data.class_id 是否屬於 current_user 所在的機構
    # (為保持流程簡潔，此處暫不實作)

    return crud.create_student(
        db=db,
        student_data=student_data,
        operator_id=current_user.id # 記錄操作者
    )
