from pydantic import BaseModel, Field
from .models import UserRole, StudentStatus
from datetime import datetime
from typing import List, Optional # 確保匯入了 List 和 Optional

# --- 機構相關 ---
class InstitutionBase(BaseModel):
    name: str

class InstitutionCreate(InstitutionBase):
    code: str

class InstitutionOut(InstitutionBase):
    id: int
    code: str

    class Config:
        from_attributes = True

# --- 使用者相關 ---
class UserBase(BaseModel):
    """使用者模型的基礎，包含通用欄位。"""
    phone_number: str
    full_name: Optional[str] = None

    
# --- User ---
class UserCreate(BaseModel):
    phone_number: str
    password: str = Field(min_length=8)
    full_name: str

# 現在，下面的 UserOut 才能正確找到它繼承的對象
class UserOut(UserBase):
    id: int
    role: UserRole
    institution: Optional[InstitutionOut] = None

    class Config:
        from_attributes = True



# --- Token ---
class Token(BaseModel):
    access_token: str
    token_type: str

# --- Teacher ---
class TeacherCreate(BaseModel):
    phone_number: str
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole = Field(default=UserRole.teacher, description="可以是 'teacher' 或 'admin'")

# --- Student ---
class StudentBase(BaseModel):
    full_name: str

class StudentCreate(StudentBase):
    pass

class StudentOut(StudentBase):
    id: int
    status: StudentStatus
    teacher: Optional[UserOut] = None
    # --- 新增 institution 欄位 ---
    institution: Optional[InstitutionOut] = None

    class Config:
        from_attributes = True

# --- Pickup Notification ---
class PickupNotificationCreate(BaseModel):
    student_id: int

class PickupNotificationOut(BaseModel):
    id: int
    student_id: int
    parent_id: int
    created_at: datetime
    status: str
    student: StudentOut

    class Config:
        orm_mode = True

class PickupNotificationCompleteOut(BaseModel):
    message: str
    notification_id: int
    student_final_status: StudentStatus

    class Config:
        orm_mode = True

        # ... (檔案上方原有的模型保持不變) ...

# --- 用於使用者修改自己密碼的模型 ---
class UserUpdatePassword(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)

# --- 用於管理員重設使用者密碼的模型 ---
class AdminResetPassword(BaseModel):
    new_password: str = Field(min_length=8)


    # ... (檔案上方原有的模型保持不變) ...

# --- 用於智慧預測提示的模型 ---
class PickupPredictionOut(BaseModel):
    prediction_date: datetime
    student: StudentOut # 直接複用我們已有的 StudentOut 模型

    class Config:
        from_attributes = True



# --- 學生相關 ---
class StudentCreateByTeacher(BaseModel):
    """老師新增學生時使用的模型"""
    full_name: str

# --- 家長綁定相關 ---
class ParentClaimStudent(BaseModel):
    """家長認領學生時使用的模型"""
    institution_code: str
    student_full_name: str