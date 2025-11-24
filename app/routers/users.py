# 檔案路徑: app/routers/users.py
# 版本：基於新憲法的 v2.0
# 說明：實現了使用者獲取自身資訊和修改密碼的核心 API。

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas, security
from ..dependencies import get_db

router = APIRouter()

@router.get("/me", response_model=schemas.UserOut, summary="獲取當前使用者資訊")
def read_users_me(current_user: models.User = Depends(security.get_current_active_user)):
    """
    獲取當前已登入使用者的詳細資訊。
    """
    return current_user

@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT, summary="使用者修改自己的密碼")
def update_my_password(
    password_data: schemas.UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """
    使用者修改自己的登入密碼。
    - 需要提供舊密碼進行驗證。
    """
    # 驗證舊密碼是否正確
    if not security.verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="舊密碼不正確")
    
    # 更新為新密碼
    crud.update_user_password(db, user=current_user, new_password=password_data.new_password)
    
    return

# 根據新憲法，家長認領學生的功能被移至一個獨立的 API，
# 而不是放在 /users/me/children，這樣更符合 RESTful 設計。
# 我們將在下一個階段重構 teachers 路由時，一併加入「家長認領學生」的 API。
