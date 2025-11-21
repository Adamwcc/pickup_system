from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas, models, security
from ..dependencies import get_db, get_current_user

router = APIRouter()

@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT, summary="使用者修改自己的密碼")
def update_current_user_password(
    password_data: schemas.UserUpdatePassword,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    已登入的使用者修改自己的密碼。
    需要提供舊密碼和新密碼。
    """
    # 1. 驗證舊密碼是否正確
    if not security.verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="舊密碼不正確"
        )
    
    # 2. 更新為新密碼
    crud.update_user_password(db, user_id=current_user.id, new_password=password_data.new_password)
    
    return

# --- 新增以下 API ---
@router.post("/me/claim-student", response_model=schemas.StudentOut, summary="家長認領學生")
def claim_student_by_parent(
    claim_data: schemas.ParentClaimStudent,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    由已登入的家長，透過「機構代碼」和「學生姓名」來綁定自己的孩子。

    - **需要家長登入權限**
    """
    student = crud.claim_student(
        db=db,
        parent_id=current_user.id,
        institution_code=claim_data.institution_code,
        student_name=claim_data.student_full_name
    )
    if not student:
        raise HTTPException(
            status_code=404, 
            detail="綁定失敗：找不到對應的機構代碼或學生姓名，或該學生已被其他家長綁定"
        )
    return student