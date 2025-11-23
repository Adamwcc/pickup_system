# 檔案路徑: pickup_system/app/routers/teachers.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..dependencies import get_db, get_current_teacher_user

# 這一行至關重要！
router = APIRouter()

@router.post("/students/", response_model=schemas.StudentOut, summary="老師新增學生並邀請家長")
def create_student_by_teacher(
    student_data: schemas.StudentCreateByTeacher,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(get_current_teacher_user)
):
    """
    由已登入的老師或管理員，在其所屬的機構下建立一位新學生，
    並為其關聯的家長建立「預註冊(invited)」帳號。
    """
    if not current_teacher.institution_id:
        raise HTTPException(status_code=400, detail="操作失敗：您的帳號未歸屬任何機構")
    
    if not student_data.parents:
        raise HTTPException(status_code=400, detail="操作失敗：必須提供至少一位家長的資訊")

    # 1. 建立學生
    student = crud.create_student_for_institution(
        db=db, 
        full_name=student_data.student_full_name, 
        institution_id=current_teacher.institution_id
    )

    # 2. 為每一位提供的家長建立預註冊帳號並綁定
    for parent_info in student_data.parents:
        crud.pre_register_parent_and_link_student(
            db=db,
            student_id=student.id,
            parent_phone=parent_info.phone_number,
            parent_full_name=parent_info.full_name
        )
    
    # 重新查詢學生資訊以包含最新的關聯
    db.refresh(student)
    return student


@router.patch(
    "/students/{student_id}/status/can-be-picked-up",
    response_model=schemas.StudentOut,
    summary="老師手動將學生標記為'可接送'"
)
def mark_student_as_can_be_picked_up(
    student_id: int,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(get_current_teacher_user)
):
    """
    老師手動將 '在班' 狀態的學生，更新為 '可接送' 狀態。
    這通常發生在學生完成了當天的進度後。
    """
    student = crud.get_student_by_id(db, student_id=student_id)
    if not student:
        raise HTTPException(status_code=404, detail="找不到該學生")

    # 權限檢查：確保操作的老師和學生在同一個機構
    if student.institution_id != current_teacher.institution_id:
        raise HTTPException(status_code=403, detail="權限不足，無法操作非本機構的學生")

    if student.status != models.StudentStatus.in_class:
        raise HTTPException(status_code=400, detail=f"學生目前狀態為'{student.status.value}'，無法標記為可接送")

    return crud.update_student_status(db, student_id=student_id, new_status=models.StudentStatus.can_be_picked_up)


@router.patch(
    "/students/{student_id}/status/homework-pending",
    response_model=schemas.StudentOut,
    summary="老師將學生標記為'作業較多'"
)
async def mark_student_as_homework_pending(
    student_id: int,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(get_current_teacher_user)
):
    """
    老師將學生狀態標記為 '作業較多'，並向其所有家長推送即時通知。
    """
    student = crud.get_student_by_id(db, student_id=student_id)
    if not student:
        raise HTTPException(status_code=404, detail="找不到該學生")

    # 權限檢查
    if student.institution_id != current_teacher.institution_id:
        raise HTTPException(status_code=403, detail="權限不足，無法操作非本機構的學生")

    updated_student = crud.update_student_status(db, student_id=student_id, new_status=models.StudentStatus.homework_pending)
    
    # --- 推送即時通知 ---
    message = f"老師提醒：{student.full_name} 目前作業較多，請您稍後再出發。"
    event_data = {
        "event": "STUDENT_STATUS_UPDATE",
        "message": message,
        "student_id": student.id,
        "new_status": models.StudentStatus.homework_pending.value
    }
    
    # 向該學生的每一位家長推送個人訊息
    if student.parents:
        for parent in student.parents:
            await crud.send_personal_message(parent.id, event_data)

    return updated_student
