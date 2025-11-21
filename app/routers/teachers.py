# 檔案路徑: pickup_system/app/routers/teachers.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas, models
from ..dependencies import get_db, get_current_teacher_user
from ..routers.websockets import manager # 確保從正確的路徑匯入 manager

router = APIRouter()

@router.patch(
    "/students/{student_id}/status/can-be-picked-up",
    response_model=schemas.StudentOut,
    summary="將學生標記為可接送"
)
def mark_student_as_can_be_picked_up(
    student_id: int,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(get_current_teacher_user)
):
    """
    老師將自己班上的某個學生狀態標記為「可接送」。
    這個操作目前不會主動推播通知，而是等待家長發起接送時，狀態檢查會通過。
    """
    # 1. 權限與學生存在性驗證
    student = crud.get_student_by_id(db, student_id=student_id)
    if not student:
        raise HTTPException(status_code=404, detail="找不到該學生")
    if student.teacher_id != current_teacher.id:
        raise HTTPException(status_code=403, detail="權限不足，這不是您班上的學生")

    # 2. 業務邏輯檢查：只有「在班」的學生才能被標記為「可接送」
    if student.status != models.StudentStatus.in_class:
        raise HTTPException(
            status_code=400,
            detail=f"操作無效：學生 {student.full_name} 目前狀態為 '{student.status.value}'，無法標記為可接送"
        )

    # 3. 更新學生狀態
    return crud.update_student_status(
        db, student_id=student_id, new_status=models.StudentStatus.can_be_picked_up
    )

@router.patch(
    "/students/{student_id}/status/homework-pending",
    response_model=schemas.StudentOut,
    summary="將學生標記為作業較多"
)
async def mark_student_as_homework_pending(
    student_id: int,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(get_current_teacher_user)
):
    """
    老師將自己班上的某個學生狀態標記為「作業較多」。
    這個操作會觸發一個 WebSocket 推播給該學生的所有家長。
    """
    # 1. 權限與學生存在性驗證
    student = crud.get_student_by_id(db, student_id=student_id)
    if not student:
        raise HTTPException(status_code=404, detail="找不到該學生")
    if student.teacher_id != current_teacher.id:
        raise HTTPException(status_code=403, detail="權限不足，這不是您班上的學生")

    # 2. 更新學生狀態
    updated_student = crud.update_student_status(
        db, student_id=student_id, new_status=models.StudentStatus.homework_pending
    )
    if not updated_student:
        raise HTTPException(status_code=500, detail="更新學生狀態失敗")

    # 3. 向所有家長推送 WebSocket 通知
    notification_payload = {
        "event": "STUDENT_STATUS_UPDATE",
        "student_id": student.id,
        "student_name": student.full_name,
        "new_status": models.StudentStatus.homework_pending.value,
        "message": f"老師提醒：{student.full_name} 目前作業較多，請您稍後再出發。"
    }
    
    if student.parents:
        for parent in student.parents:
            await manager.send_personal_message(notification_payload, user_id=parent.id)

    return updated_student

    # --- 新增以下 API ---
@router.post("/students/", response_model=schemas.StudentOut, summary="老師新增學生")
def create_student_by_teacher(
    student_data: schemas.StudentCreateByTeacher,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(get_current_teacher_user)
):
    """
    由已登入的老師或管理員，在其所屬的機構下建立一位新學生。

    - **需要老師或管理員權限**
    """
    if not current_teacher.institution_id:
        raise HTTPException(status_code=400, detail="操作失敗：您的帳號未歸屬任何機構")
    
    return crud.create_student_for_institution(
        db=db, 
        full_name=student_data.full_name, 
        institution_id=current_teacher.institution_id
    )

