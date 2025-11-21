from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..routers.websockets import manager

from .. import crud, schemas, models
from ..dependencies import get_db, get_current_teacher_user # <--- 我們將在下一步建立這個依賴

router = APIRouter()

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
    # ... (此函式的內容與我上一則訊息中的完全一樣，請直接複製過來) ...
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
