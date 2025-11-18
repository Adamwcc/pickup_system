from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas, models
from ..dependencies import get_db, get_current_admin_user

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
    
    # 使用新的 crud 函式來建立教職員
    return crud.create_teacher(db=db, user=teacher_data)


    # ... (檔案上方原有的 create_new_teacher 函式保持不變) ...

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

