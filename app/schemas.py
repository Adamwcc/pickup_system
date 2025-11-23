# 檔案路徑: app/schemas.py
# 這是重構的核心，統一了所有資料模型的命名。

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .models import UserRole, StudentStatus, UserStatus

# ===================================================================
# 基礎模型 (Base) - 定義通用欄位
# ===================================================================

class UserBase(BaseModel):
    phone_number: str = Field(..., example="0912345678")
    full_name: Optional[str] = Field(None, example="王大明")

class StudentBase(BaseModel):
    full_name: str = Field(..., example="王小明")

class InstitutionBase(BaseModel):
    name: str = Field(..., example="快樂兒童安親班")
    code: str = Field(..., example="HAPPY-KIDS-123")

# ===================================================================
# 輸入模型 (In) - 用於建立 (Create) 和更新 (Update)
# ===================================================================

# --- 機構 ---
class InstitutionCreate(InstitutionBase):
    pass

# --- 使用者 ---
class UserCreate(UserBase):
    """ 用於管理員建立任何角色的使用者 """
    password: str = Field(..., min_length=8)
    role: UserRole = Field(default=UserRole.parent)

class ParentInvite(UserBase):
    """ 用於老師新增學生時，順帶邀請的家長資訊 """
    pass

class UserPasswordUpdate(BaseModel):
    """ 用於使用者更新自己的密碼 """
    old_password: str
    new_password: str = Field(min_length=8)

class AdminPasswordReset(BaseModel):
    """ 用於管理員重設使用者的密碼 """
    new_password: str = Field(min_length=8)

# --- 學生 ---
class StudentCreate(BaseModel):
    """ 用於老師建立新學生，並可選擇性地邀請家長 """
    student_full_name: str
    parents: List[ParentInvite] = []

class StudentStatusUpdate(BaseModel):
    """ 用於老師更新學生狀態 """
    status: StudentStatus

class StudentClaim(BaseModel):
    """ 用於家長認領學生 """
    institution_code: str
    student_name: str

# --- 接送 ---
class PickupNotificationCreate(BaseModel):
    student_id: int

# ===================================================================
# 輸出模型 (Out) - 用於 API 回傳
# ===================================================================

class InstitutionOut(InstitutionBase):
    id: int
    class Config:
        from_attributes = True

class UserOut(UserBase):
    id: int
    role: UserRole
    status: UserStatus
    institution: Optional[InstitutionOut] = None
    class Config:
        from_attributes = True

class StudentOut(StudentBase):
    id: int
    status: StudentStatus
    is_active: bool
    teacher: Optional[UserOut] = None
    parents: List[UserOut] = []
    institution: Optional[InstitutionOut] = None
    class Config:
        from_attributes = True

class PickupNotificationOut(BaseModel):
    id: int
    student_id: int
    parent_id: int
    status: str
    created_at: datetime
    student: StudentOut
    parent: UserOut
    class Config:
        from_attributes = True

class PickupPredictionOut(BaseModel):
    id: int
    prediction_date: datetime
    student_id: int
    reason: Optional[str] = None
    student: StudentOut
    class Config:
        from_attributes = True

# ===================================================================
# 認證模型 (Auth)
# ===================================================================

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    phone_number: Optional[str] = None

class UserActivation(BaseModel):
    """ 用於 'invited' 狀態的家長啟用自己的帳號 """
    phone_number: str
    password: str = Field(min_length=8)

