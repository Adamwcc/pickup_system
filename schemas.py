from pydantic import BaseModel
from typing import Optional

# Pydantic 模型用於資料驗證和序列化

class UserBase(BaseModel):
    phone_number: str
    full_name: str
    role: Optional[str] = "parent"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: str # 為了簡化，直接使用字串表示時間

    class Config:
        orm_mode = True # 允許從 ORM 模型直接轉換
