from fastapi import APIRouter, Depends, HTTPException, status # <--- 確保 status 在這裡
from sqlalchemy.orm import Session

from .. import crud, schemas, models
from ..dependencies import get_db, get_current_admin_user
from ..jobs import prediction_job # <--- 在檔案頂部附近新增這一行

router = APIRouter()

@router.post("/teachers", response_model=schemas.UserOut, summary="新增教職員帳號")
def create_new_teacher(
    teacher_data: schemas.TeacherCreate,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    """
    由管理員 (admin) 建立一個新的教職員 (teacher) 或另一個管理員帳號。

    - **需要管理員權限**
    """
    db_user = crud.get_user_by_phone(db, phone_number=teacher_data.phone_number)
    if db_user:
        raise HTTPException(status_code=400, detail="此手機號碼已被註冊")
    
    return crud.create_teacher(db=db, user=teacher_data)

@router.delete("/users/{user_id}", response_model=schemas.UserOut, summary="停用使用者帳號 (邏輯刪除)")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    """
    由管理員停用一個使用者帳號（老師或家長）。
    這是一個邏輯刪除，資料會被保留。
    """
    user_to_delete = crud.get_user_by_id(db, user_id)
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="找不到該使用者")
    
    if user_to_delete.id == admin_user.id:
        raise HTTPException(status_code=400, detail="管理員無法停用自己的帳號")

    return crud.deactivate_user(db=db, user_id=user_id)

@router.delete("/students/{student_id}", response_model=schemas.StudentOut, summary="刪除學生資料 (邏輯刪除)")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    """
    由管理員刪除一個學生。
    這是一個邏輯刪除，資料會被保留。
    """
    student_to_delete = crud.get_student_by_id(db, student_id)
    if not student_to_delete:
        raise HTTPException(status_code=404, detail="找不到該學生")

    return crud.deactivate_student(db=db, student_id=student_id)

@router.patch(
    "/users/{user_id}/password", 
    status_code=status.HTTP_204_NO_CONTENT, 
    summary="管理員重設使用者密碼"
)
def admin_reset_user_password(
    user_id: int,
    password_data: schemas.AdminResetPassword,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    """
    由管理員強制重設指定使用者的密碼，無需知道舊密碼。
    """
    user_to_update = crud.get_user_by_id(db, user_id)
    if not user_to_update:
        raise HTTPException(status_code=404, detail="找不到該使用者")

    if user_to_update.id == admin_user.id:
        raise HTTPException(
            status_code=400, 
            detail="請使用'修改自己的密碼'功能來更改您的密碼"
        )

    crud.update_user_password(db, user_id=user_id, new_password=password_data.new_password)
    
    return


    # ... (檔案上方原有的函式保持不變) ...

# --- 匯入我們需要的新模組 ---

@router.post(
    "/jobs/trigger-prediction", 
    summary="手動觸發智慧預測分析任務",
    include_in_schema=True # 設定為 True 讓它顯示在文件中，方便我們測試
)
def trigger_prediction_job(
    admin_user: models.User = Depends(get_current_admin_user)
):
    """
    由管理員手動觸發一次歷史數據分析與預測任務。
    這是一個臨時的解決方案，用於在無法使用 Cron Job 的環境中進行測試。
    """
    try:
        prediction_job.analyze_and_predict()
        return {"message": "智慧預測任務已成功觸發並執行完畢。"}
    except Exception as e:
        # 捕獲任何潛在的錯誤，並以清晰的方式回傳
        raise HTTPException(
            status_code=500,
            detail=f"執行預測任務時發生錯誤: {str(e)}"
        )

