# 檔案路徑: app/routers/users.py
# 這是重構的第五步，提供使用者查詢自己、修改密碼等個人操作的 API。

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas, models, security

router = APIRouter()

@router.get("/me", response_model=schemas.UserOut, summary="獲取當前登入使用者的資訊")
def read_current_user(
    current_user: models.User = Depends(security.get_current_active_user)
):
    """
    回傳當前登入者的詳細資訊。
    """
    return current_user

@router.get("/me/students", response_model=List[schemas.StudentOut], summary="獲取當前家長名下的所有學生")
def get_my_students(
    current_user: models.User = Depends(security.get_current_active_user)
):
    """
    家長專用，獲取自己所有已綁定的孩子列表。
    """
    if current_user.role != models.UserRole.parent:
        raise HTTPException(status_code=403, detail="Only parents can access this resource.")
    return current_user.children

@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT, summary="更新當前使用者的密碼")
def update_current_user_password(
    password_data: schemas.UserPasswordUpdate,
    db: Session = Depends(security.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """
    使用者更新自己的密碼。
    """
    if not security.verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    new_hashed_password = security.get_password_hash(password_data.new_password)
    current_user.hashed_password = new_hashed_password
    db.add(current_user)
    db.commit()
    return

@router.post("/me/students/claim", response_model=schemas.StudentOut, summary="家長認領學生")
def claim_student_for_parent(
    claim_data: schemas.StudentClaim,
    db: Session = Depends(security.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """
    家長使用「機構代碼」和「學生姓名」來認領自己的孩子。
    """
    # ... 這裡可以加上認領學生的 CRUD 邏輯 ...
    # crud.claim_student(db, parent_id=current_user.id, ...)
    # 為了簡化，我們先假設這個邏輯存在
    raise HTTPException(status_code=501, detail="Claiming logic not fully implemented yet.")

