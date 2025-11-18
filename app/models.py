from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base
import enum
from datetime import datetime

# --- Enums ---
class UserRole(str, enum.Enum):
    parent = "parent"
    teacher = "teacher"
    admin = "admin"

class StudentStatus(str, enum.Enum):
    in_class = "在校"
    waiting_pickup = "等待接送"
    departed = "已離校"

# --- 中間表 (Association Table) ---
class ParentStudentLink(Base):
    __tablename__ = "parent_student_link"
    parent_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), primary_key=True)

# --- 主要模型 (Primary Models) ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.parent)
    is_active = Column(Boolean, default=True) # <--- 新增這一行
    
    # 使用 back_populates 來建立雙向關聯，這更為穩健
    children = relationship(
        "Student", 
        secondary="parent_student_link", 
        back_populates="parents"
    )

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True, nullable=False)
    status = Column(Enum(StudentStatus), default=StudentStatus.in_class)
    is_active = Column(Boolean, default=True) # <--- 新增這一行
    
    parents = relationship(
        "User", 
        secondary="parent_student_link", 
        back_populates="children"
    )
    
    notifications = relationship("PickupNotification", back_populates="student")

class PickupNotification(Base):
    __tablename__ = "pickup_notifications"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active") # active, completed, cancelled
    
    student = relationship("Student", back_populates="notifications")
    parent = relationship("User")
