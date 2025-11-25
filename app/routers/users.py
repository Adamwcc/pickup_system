# 檔案路徑: app/routers/users.py
# 版本：基於新憲法的 v2.0
# 說明：實現了使用者獲取自身資訊和修改密碼的核心 API。

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas, security
from ..dependencies import get_db

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
    dependencies=[Depends(security.get_current_active_user)], # <--- 將通用依賴放在這裡
    responses={404: {"description": "Not found"}},
)

@router.get("/me", response_model=schemas.UserDetail)
def read_users_me(current_user: models.User = Depends(security.get_current_active_user)): # 保持顯式依賴以獲取 user 物件
    """ 獲取當前登入使用者的完整資訊。 """
    return current_user


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def update_my_password(
    password_data: schemas.UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user) # 這裡的用法是正確的
):
    """ 使用者修改自己的登入密碼。 """
    if not security.verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="舊密碼不正確")
    
    crud.update_user_password(db, user=current_user, new_password=password_data.new_password)
    return


@router.post("/me/children", response_model=schemas.UserDetail)
def bind_additional_child(
    binding_data: schemas.ChildBindingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user) # <--- 確保這裡也使用正確的引用
):
    """ 為當前家長綁定一個額外的子女。 """
    updated_user = crud.bind_child_to_parent(
        db=db, 
        parent=current_user, 
        child_info=binding_data
    )
    return updated_user