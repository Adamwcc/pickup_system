from pydantic import BaseModel, Field
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
