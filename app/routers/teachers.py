# 檔案路徑: pickup_system/app/routers/teachers.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# 確保匯入所有需要的模組
from .. import crud, models, schemas, security 
from ..database import get_db

# --- 1. 定義一個清晰、可複用的權限依賴 ---
def get_current_teacher_or_admin(current_user: models.User = Depends(security.get_current_active_user)):
    """
    一個依賴項，用於驗證當前使用者是否為 'teacher' 或 'admin'。
    """
    if current_user.role not in [models.UserRole.teacher, models.UserRole.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Requires teacher or admin privileges."
        )
    return current_user

# --- 2. 建立路由器實例 ---
router = APIRouter()

# --- 3. 融合後的、唯一的「建立學生」API ---
@router.post("/students/", response_model=schemas.StudentOut, status_code=status.HTTP_201_CREATED, summary="老師新增學生並邀請家長")
def create_student_and_invite_parents(
    student_data: schemas.StudentCreateByTeacher, # 繼續使用您設計的、支援多家長的輸入模型
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_teacher_or_admin) # 使用新的、更通用的權限依賴
):
    """
    由已登入的老師或管理員，在其所屬的機構下建立一位新學生，
    並可選擇性地為一位或多位家長建立「預註冊(invited)」帳號並完成綁定。
    """
    if not current_user.institution_id:
        raise HTTPException(status_code=400, detail="操作失敗：您的帳號未歸屬任何機構")
    
    # 我們需要稍微修改 CRUD 函式來配合這個 API
    # 這裡假設 crud.create_student_and_parents 是一個新的、更強大的 CRUD 函式
    
    try:
        db_student = crud.create_student_and_invite_parents(
            db=db,
            student_name=student_data.student_full_name,
            parents_data=student_data.parents,
            teacher_id=current_user.id,
            institution_id=current_user.institution_id
        )
        return db_student
    except Exception as e:
        # 捕獲潛在的錯誤，例如資料庫操作失敗
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


# --- 4. 保留其他有用的 API 端點 ---

@router.patch("/students/{student_id}/status/{new_status}", response_model=schemas.StudentOut, summary="老師更新學生狀態")
async def update_student_status_by_teacher(
    student_id: int,
    new_status: models.StudentStatus, # 使用路徑參數，更符合 RESTful 風格
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_teacher_or_admin)
):
    """
    老師更新指定學生的狀態。
    - 如果狀態更新為 'homework_pending'，將會向家長推送即時通知。
    """
    student = crud.get_student_by_id(db, student_id=student_id)
    if not student:
        raise HTTPException(status_code=404, detail="找不到該學生")

    # 權限檢查：確保操作的老師和學生在同一個機構
    if student.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="權限不足，無法操作非本機構的學生")

    # 執行狀態更新
    updated_student = crud.update_student_status(db, student_id=student_id, new_status=new_status)
    
    # 如果狀態是 '作業較多'，則觸發通知
    if new_status == models.StudentStatus.homework_pending:
        message = f"老師提醒：{student.full_name} 目前作業較多，請您稍後再出發。"
        event_data = {
            "event": "STUDENT_STATUS_UPDATE",
            "message": message,
            "student_id": student.id,
            "new_status": new_status.value
        }
        
        if student.parents:
            for parent in student.parents:
                # 假設 crud.send_personal_message 存在
                await crud.send_personal_message(parent.id, event_data)

    return updated_student

