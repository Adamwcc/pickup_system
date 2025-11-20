from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, schemas, models
from ..dependencies import get_db, get_current_user

router = APIRouter()

@router.get("/students", response_model=List[schemas.StudentOut], summary="獲取儀表板學生列表（動態篩選）")
def get_dashboard_student_list(
    teacher_id: Optional[int] = None,
    status: Optional[List[models.StudentStatus]] = Query(None), # 使用 Query 來接收多個同名參數
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    一個統一的 API，用於獲取儀表板所需的學生列表，支持靈活的篩選和排序。

    - **權限**: `teacher`, `receptionist`, `admin` 可用。
    - **篩選**:
        - `teacher_id`: 篩選特定老師的學生。
        - `status`: 篩選一個或多個狀態 (例如: `?status=在班&status=可接送`)。
    - **排序**: 結果會自動按 `家長已出發` > `可接送` > `在班` > `已離校` 的順序排列。
    """
    # --- 權限校驗 ---
    allowed_roles = [models.UserRole.teacher, models.UserRole.receptionist, models.UserRole.admin]
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="權限不足")

    # --- 參數校驗與修正 ---
    # 如果是普通老師，強制只能查詢自己的班級
    if current_user.role == models.UserRole.teacher:
        if teacher_id is not None and teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="權限不足，您只能查詢自己班級的學生")
        # 如果老師沒提供 teacher_id，自動設為他自己的 ID
        teacher_id = current_user.id

    # --- 呼叫核心查詢函式 ---
    students = crud.get_dashboard_students(db, teacher_id=teacher_id, statuses=status)
    return students
