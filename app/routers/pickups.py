from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas, models
from ..dependencies import get_db, get_current_user
from typing import List # <--- 確保在檔案頂部匯入了 List
from datetime import datetime # <--- 確保在檔案頂部匯入了 datetime

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

# ... (檔案上方原有的 start_pickup_process 函式保持不變) ...

@router.post(
    "/{notification_id}/complete", 
    response_model=schemas.PickupNotificationCompleteOut, 
    summary="教職員確認完成交接"
)
def complete_pickup(
    notification_id: int,
    db: Session = Depends(get_db),
    # 這裡我們先用 get_current_user，代表任何登入者都能操作
    # 未來可以改成只允許 teacher 或 admin
    current_user: models.User = Depends(get_current_user) 
):
    """
    由教職員操作，標記一個接送通知已完成，並更新學生狀態為'已離校'。

    - **需要登入權限**
    """
    notification = crud.get_notification_by_id(db, notification_id=notification_id)
    
    # 驗證1：通知是否存在
    if not notification:
        raise HTTPException(status_code=404, detail="找不到該接送通知")

    # 驗證2：通知是否處於可完成的狀態
    if notification.status != "active":
        raise HTTPException(status_code=400, detail=f"該通知狀態為'{notification.status}'，無法完成")

    # 執行完成操作
    completed_notification = crud.complete_pickup_notification(db=db, notification_id=notification_id)
    
    return {
        "message": "交接成功完成！",
        "notification_id": completed_notification.id,
        "student_final_status": completed_notification.student.status
    }

# ... (檔案上方原有的函式保持不變) ...


@router.get("/predictions/today", response_model=List[schemas.PickupPredictionOut], summary="獲取今日的智慧預測列表")
def get_today_predictions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # 確保只有登入使用者能看
):
    """
    獲取系統根據歷史數據分析出的，今天最有可能被接送的「常客」學生列表。
    """
    today = datetime.utcnow().date()
    predictions = db.query(models.PickupPrediction).filter(func.date(models.PickupPrediction.prediction_date) == today).all()
    return predictions
