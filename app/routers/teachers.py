from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas, models
from ..dependencies import get_db, get_current_teacher_user # <--- 我們將在下一步建立這個依賴

router = APIRouter()

@router.get("/my-students", response_model=List[schemas.StudentOut], summary="獲取我班上的所有學生")
def get_my_students(
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(get_current_teacher_user)
):
    """
    獲取當前登入老師名下的所有學生列表。
    管理員呼叫此 API 時，會因為其也屬於 'teacher' 角色而成功，
    但這裡只會回傳 teacher_id 與其自身 ID 匹配的學生。
    """
    return crud.get_students_by_teacher(db, teacher_id=current_teacher.id)


@router.patch("/students/{student_id}/status/can-be-picked-up", response_model=schemas.StudentOut, summary="標記學生為'可接送'")
def mark_student_as_ready(
    student_id: int,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(get_current_teacher_user)
):
    """
    由帶班老師將自己班上的學生狀態更新為'可接送'。
    這個動作會觸發一個給家長的通知（模擬）。
    """
    db_student = crud.get_student_by_id(db, student_id=student_id)

    # --- 權限驗證 ---
    if not db_student:
        raise HTTPException(status_code=404, detail="找不到該學生")
    
    # 核心權限檢查：確保要操作的學生，其 teacher_id 與當前登入的老師 ID 相同
    if db_student.teacher_id != current_teacher.id:
        raise HTTPException(status_code=403, detail="權限不足：這不是您班上的學生")

    # --- 更新狀態 ---
    updated_student = crud.update_student_status(db, student_id=student_id, new_status=models.StudentStatus.can_be_picked_up)
    
    # --- (模擬) 觸發家長通知 ---
    print(f"--- 推播通知 ---")
    print(f"正在向學生 {db_student.full_name} 的家長發送通知：課程已完成，可以準備接送了。")
    print(f"-----------------")

    return updated_student
