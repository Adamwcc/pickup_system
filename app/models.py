from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String, default="parent") # 'parent', 'teacher', 'admin'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    # 未來可以添加關係
    # children = relationship("Student", back_populates="parent")
