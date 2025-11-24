# 檔案路徑: app/schemas.py
# 這是基於新憲法的第二步，提供了與新 models 完全對應的 API 資料模型。

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .models import UserRole, StudentStatus, UserStatus

# ===================================================================
# 基礎與輸出模型 (Base & Out)
# ===================================================================

class InstitutionOut(BaseModel):
    id: int
    name: str
    code: str
    class Config:
        from_attributes = True

class ClassOut(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class UserOut(BaseModel):
    id: int
    phone_number: str
    full_name: str
    role: UserRole
    status: UserStatus
    class Config:
        from_attributes = True

class StudentOut(BaseModel):
    id: int
    full_name: str
    status: StudentStatus
    class_: Optional[ClassOut] = Field(None, alias="class") # API回傳時用 'class'
    parents: List[UserOut] = []
    class Config:
        from_attributes = True
        populate_by_name = True # 允許 alias

# ===================================================================
# 輸入模型 (In) - 用於 API 請求
# ===================================================================

# --- 機構 Admin ---
class InstitutionCreate(BaseModel):
    name: str = Field(..., example="快樂兒童安親班")
    code: str = Field(..., example="HAPPY-KIDS-123")

class StaffCreate(BaseModel):
    phone_number: str = Field(..., example="0987654321")
    full_name: str = Field(..., example="王老師")
    password: str = Field(..., min_length=8)
    role: UserRole = Field(..., example="teacher") # 必須是 teacher, receptionist, 或 admin

class ClassCreate(BaseModel):
    name: str = Field(..., example="小一數學班")
    teacher_id: Optional[int] = None

# --- 老師 Teacher ---
class ParentInvite(BaseModel):
    phone_number: str = Field(..., example="0912345678")
    full_name:  Optional[str] = None

class StudentCreate(BaseModel):
    full_name: str = Field(..., example="王小明")
    class_id: int
    parents: List[ParentInvite] = []

class StudentStatusUpdate(BaseModel):
    status: StudentStatus

# --- 家長 Parent ---
class ParentActivate(BaseModel):
    phone_number: str
    password: str = Field(min_length=8)
    institution_code: str
    student_name: str


"""家長啟用帳號"""
class ParentActivation(BaseModel):
    """家長啟用帳號時，需要提供的資料。"""
    phone_number: str = Field(..., description="家長的手機號碼")
    password: str = Field(..., min_length=8, description="家長自訂的密碼")
    institution_code: str = Field(..., description="機構的唯一代碼")
    student_full_name: str = Field(..., description="家長其中一位孩子的姓名，用於驗證身份")


# ===================================================================
# User Self-Service (使用者自助服務)
# ===================================================================

class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)


class PickupStart(BaseModel):
    student_id: int

# ===================================================================
# 認證模型 (Auth)
# ===================================================================

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    phone_number: Optional[str] = None



