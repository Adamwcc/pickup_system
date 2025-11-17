from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
import enum
from datetime import datetime

# --- 原有的 UserRole 和 User 模型 ---
class UserRole(str, enum.Enum):
    parent = "parent"
    teacher = "teacher"
    admin = "admin"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.parent)
    
    # 建立 User 和 Student 之間的關聯
    children = relationship("Student", secondary="parent_student_link")

# --- 新增的學生狀態 Enum ---
class StudentStatus(str, enum.Enum):
    in_class = "在校"
    waiting_pickup = "等待接送"
    departed = "已離校"

# --- 新增的 Student 模型 ---
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True, nullable=False)
    status = Column(Enum(StudentStatus), default=StudentStatus.in_class)
    
    parents = relationship("User", secondary="parent_student_link")

# --- 新增的 ParentStudentLink 中間表 ---
class ParentStudentLink(Base):
    __tablename__ = "parent_student_link"
    parent_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), primary_key=True)

# --- 新增的 PickupNotification 模型 ---
class PickupNotification(Base):
    __tablename__ = "pickup_notifications"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active") # active, completed, cancelled
    
    student = relationship("Student")
    parent = relationship("User")
