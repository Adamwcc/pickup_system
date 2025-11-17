from pydantic import BaseModel, Field
from .models import UserRole, StudentStatus  # <--- 在這裡新增 StudentStatus
from datetime import datetime # <--- 我們也需要這個，為 PickupNotificationOut 做準備
from .models import UserRole

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

class Token(BaseModel):
    access_token: str
    token_type: str
# ... (檔案上方原有的 UserCreate, UserOut, Token 類別保持不變) ...

class TeacherCreate(BaseModel):
    phone_number: str
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole = Field(default=UserRole.teacher, description="可以是 'teacher' 或 'admin'")

# ... (檔案上方原有的模型保持不變) ...
from datetime import datetime

# --- 學生相關模型 ---
class StudentBase(BaseModel):
    full_name: str

class StudentCreate(StudentBase):
    pass

class StudentOut(StudentBase):
    id: int
    status: StudentStatus # <--- 現在 Python 知道 StudentStatus 是什麼了

    class Config:
        orm_mode = True

# --- 接送通知相關模型 ---
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
