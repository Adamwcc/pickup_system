from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas, models
from ..dependencies import get_db, get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.PickupNotificationOut, summary="家長發起接送通知")
def start_pickup_process(
    notification_data: schemas.PickupNotificationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    家長為其名下的某個孩子發起一個接送通知。

    - **需要家長登入權限**
    """
    student_id = notification_data.student_id
    
    # 驗證1：學生是否存在
    student = crud.get_student_by_id(db, student_id=student_id)
    if not student:
        raise HTTPException(status_code=404, detail="找不到該學生")

    # 驗證2：操作者是否為該學生的家長
    is_parent_of_student = any(p.id == current_user.id for p in student.parents)
    if not is_parent_of_student:
        raise HTTPException(status_code=403, detail="權限不足，您不是該學生的家長")

    # 驗證3：學生是否處於可被接送的狀態
    if student.status != models.StudentStatus.in_class:
        raise HTTPException(status_code=400, detail=f"學生目前狀態為'{student.status.value}'，無法發起接送")

    # 建立接送通知
    return crud.create_pickup_notification(db=db, parent_id=current_user.id, student_id=student_id)
