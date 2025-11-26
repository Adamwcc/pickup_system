# 檔案路徑: app/routers/teachers.py
# 版本：v2.1 - 重構為統一使用 security 模組的權限依賴項

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas, security
from ..dependencies import get_db

# vvv--- 這是我們要修改的地方 ---vvv
# 移除本地的 get_current_teacher_or_higher 函式

router = APIRouter()
# ^^^--- 修改結束 ---^^^


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
    # 【修正】: 統一使用 security 的依賴項，並保持變數名一致
    current_teacher: models.User = Depends(security.get_current_active_teacher)
):
    """
    由已登入的教職員，在自己所屬的機構下，建立一位新學生。
    """
    # 【新增】: 可以在此加入對 institution_id 的檢查
    if not current_teacher.institution_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="操作失敗：您的帳號未歸屬任何機構。"
        )
    
    # 在 crud.create_student 中處理業務邏輯
    # 注意：您之前的程式碼呼叫了 crud.create_student，但我們之前定義的是 crud.create_student_with_parents
    # 這裡我假設您指的是後者。
    return crud.create_student_with_parents(
        db=db,
        student_data=student_data,
        teacher=current_teacher 
    )


@router.delete("/students/{student_id}/parents/{parent_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="教師職權:解除學生對家長的綁定"
)
def unbind_parent_from_student_by_teacher(
    student_id: int,
    parent_id: int,
    db: Session = Depends(get_db),
    # 【確認】: 這裡的用法是正確的
    current_teacher: models.User = Depends(security.get_current_active_teacher)
):
    """【老師/管理員】為指定學生，解除與指定家長的綁定。"""
    success = crud.unbind_student_from_parent_by_ids(
        db=db, 
        parent_id=parent_id, 
        student_id=student_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="找不到指定的學生或家長，或他們之間沒有綁定關係")
    return


@router.delete("/students/{student_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="教師職權:刪除學生帳號"
)
def delete_student_by_teacher(
    student_id: int,
    db: Session = Depends(get_db),
    # 【確認】: 這裡的用法是正確的
    current_teacher: models.User = Depends(security.get_current_active_teacher)
):
    """【老師/管理員】刪除一個學生。"""
    deleted_student = crud.delete_student_by_id(db=db, student_id=student_id)
    
    if not deleted_student:
        raise HTTPException(status_code=404, detail="找不到指定的學生")
    return
