# 檔案路徑: pickup_system/app/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional
from .models import UserRole, StudentStatus

# --- 機構相關 ---
class InstitutionOut(BaseModel):
    id: int
    name: str
    code: str

    class Config:
        from_attributes = True

# --- 使用者相關 ---
class UserBase(BaseModel):
    """使用者模型的基礎，包含通用欄位。"""
    phone_number: str
    full_name: Optional[str] = None

class UserCreate(BaseModel):
    phone_number: str
    password: str = Field(min_length=8)
    full_name: str

class UserOut(UserBase):
    id: int
    role: UserRole
    institution: Optional[InstitutionOut] = None
    status: str

    class Config:
        from_attributes = True

class UserActivate(BaseModel):
    phone_number: str
    password: str = Field(min_length=8)
    institution_code: str
    student_full_name: str

# --- 這個是我們這次補上的 ---
class TeacherCreate(BaseModel):
    phone_number: str
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole = Field(default=UserRole.teacher, description="可以是 'teacher' 或 'admin'")

# --- 學生相關 ---
class StudentBase(BaseModel):
    full_name: str

class StudentCreate(StudentBase):
    pass

class StudentOut(StudentBase):
    id: int
    status: StudentStatus
    teacher: Optional[UserOut] = None
    parents: List[UserOut] = []
    institution: Optional[InstitutionOut] = None

    class Config:
        from_attributes = True

class ParentInvite(BaseModel):
    phone_number: str
    full_name: str

class StudentCreateByTeacher(BaseModel):
    student_full_name: str
    parents: List[ParentInvite]

# --- 認證與 Token ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    phone_number: Optional[str] = None

# --- 接送流程 ---
class PickupNotificationCreate(BaseModel):
    student_id: int

class PickupNotificationOut(BaseModel):
    id: int
    student_id: int
    parent_id: int
    status: str
    student: StudentOut

    class Config:
        from_attributes = True

# --- 密碼管理 ---
class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)

class AdminPasswordReset(BaseModel):
    new_password: str = Field(min_length=8)

# --- 儀表板 ---
class DashboardStudentOut(StudentOut):
    pass
