from pydantic import BaseModel, Field
from .models import UserRole, StudentStatus
from datetime import datetime

# --- User ---
class UserCreate(BaseModel):
    phone_number: str
    password: str = Field(min_length=8)
    full_name: str

class UserOut(BaseModel):
    id: int
    phone_number: str
    full_name: str
    role: UserRole

    class Config:
        orm_mode = True

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

    class Config:
        orm_mode = True

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
