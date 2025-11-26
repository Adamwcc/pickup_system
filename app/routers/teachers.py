# 檔案路徑: app/routers/teachers.py
# 版本：v2.2 - 新增核心的學生狀態更新 API

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas, security
from ..dependencies import get_db

router = APIRouter(
    # 將通用的權限依賴項放在這裡，確保此路由下的所有 API 都需要教職員身份
    dependencies=[Depends(security.get_current_active_teacher)],
    # 為此路由下的所有 API 添加統一的 tag
    tags=["4. 教職員 (Teachers)"]
)

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
    current_teacher: models.User = Depends(security.get_current_active_teacher)
):
    """
    由已登入的教職員，在自己所屬的機構下，建立一位新學生，並同時預註冊其家長。
    """
    if not current_teacher.institution_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="操作失敗：您的帳號未歸屬任何機構。"
        )
    
    # 【Bug修復】: 呼叫我們在 crud.py 中定義的、正確的 create_student 函式
    return crud.create_student(
        db=db,
        student_data=student_data
    )

# vvv--- 【新 API】這就是我們第七階段的引擎 ---vvv
@router.patch(
    "/students/{student_id}/status",
    response_model=schemas.StudentOut,
    summary="教職員更新學生狀態"
)
def update_student_status_by_teacher(
    student_id: int,
    status_update: schemas.StudentStatusUpdate,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(security.get_current_active_teacher)
):
    """
    教職員更新學生的在校狀態。
    這是整個接送迴圈的核心驅動 API。
    - 點名: `NOT_ARRIVED` -> `ARRIVED`
    - 更新進度: `ARRIVED` -> `READY_FOR_PICKUP` / `HOMEWORK_PENDING`
    - 確認接走: `PARENT_EN_ROUTE` -> `PICKUP_COMPLETED`
    """
    # 1. 獲取學生實例
    student = crud.get_student_by_id(db, student_id=student_id)
    if not student:
        raise HTTPException(status_code=404, detail="找不到指定的學生")

    # 2. 呼叫核心業務邏輯函式
    # 所有複雜的權限檢查、狀態機驗證、推播邏輯，都封裝在 crud 函式中
    return crud.update_student_status(
        db=db,
        student=student,
        new_status=status_update.status,
        operator=current_teacher
    )
# ^^^--- 新 API 結束 ---^^^

@router.delete(
    "/students/{student_id}/parents/{parent_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="教職員解除學生綁定"
)
def unbind_parent_from_student_by_teacher(
    student_id: int,
    parent_id: int,
    db: Session = Depends(get_db),
    # current_teacher 依賴項已在 router 層級定義，此處可省略，但保留亦無妨
    current_teacher: models.User = Depends(security.get_current_active_teacher)
):
    """【教職員】為指定學生，解除與指定家長的綁定。"""
    success = crud.unbind_student_from_parent_by_ids(
        db=db, 
        parent_id=parent_id, 
        student_id=student_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="找不到指定的學生或家長，或他們之間沒有綁定關係")
    return

@router.delete(
    "/students/{student_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="教職員刪除學生"
)
def delete_student_by_teacher(
    student_id: int,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(security.get_current_active_teacher)
):
    """【教職員】刪除一個學生。"""
    deleted_student = crud.delete_student_by_id(db=db, student_id=student_id)
    if not deleted_student:
        raise HTTPException(status_code=404, detail="找不到指定的學生")
    return
