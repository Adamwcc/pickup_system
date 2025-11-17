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
