from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base
import enum
from datetime import datetime

# 位於 app/models.py 的頂部

class Institution(Base):
    __tablename__ = "institutions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)

    students = relationship("Student", back_populates="institution")
    staff = relationship("User", back_populates="institution")


# --- Enums ---

class UserStatus(str, enum.Enum):
    """使用者帳號狀態"""
    invited = "invited"      # 已被邀請，但尚未啟用
    active = "active"        # 已啟用，正常使用
    inactive = "inactive"    # 已停用/邏輯刪除

class UserRole(str, enum.Enum):
    parent = "parent"
    teacher = "teacher"
    receptionist = "receptionist" # <--- 新增這一行
    admin = "admin"


class StudentStatus(str, enum.Enum):
    in_class = "在班"
    can_be_picked_up = "可接送"
    homework_pending = "作業較多" # <--- 新增這一行
    parent_is_coming = "家長已出發" # <--- 修改這一行
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
    
    # 我們不再需要一個獨立的密碼欄位，因為 invited 狀態的使用者可以沒有密碼
    hashed_password = Column(String, nullable=True) # <--- 修改：允許為空 (nullable=True)
    
    full_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.parent)
    
    # --- 替換 is_active ---
    # is_active = Column(Boolean, default=True) # <--- 刪除或註解掉這一行
    status = Column(Enum(UserStatus), default=UserStatus.active, nullable=False) # <--- 新增這一行
    
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)

    # --- 關聯 (Relationships) 保持不變 ---
    institution = relationship("Institution")
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
    is_active = Column(Boolean, default=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
     # --- 新增以下兩行 ---
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    institution = relationship("Institution", back_populates="students")
    # --- 結束新增 ---

    parents = relationship(
        "User", 
        secondary="parent_student_link", 
        back_populates="children"
    )
    
    notifications = relationship("PickupNotification", back_populates="student")
    teacher = relationship("User") # <--- 新增這一行


class PickupNotification(Base):
    __tablename__ = "pickup_notifications"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active") # active, completed, cancelled
    
    student = relationship("Student", back_populates="notifications")
    parent = relationship("User")

    # ... (檔案上方原有的模型保持不變) ...

class PickupPrediction(Base):
    """用於儲存每日接送預測結果的資料表。"""
    __tablename__ = "pickup_predictions"

    id = Column(Integer, primary_key=True, index=True)
    prediction_date = Column(DateTime, index=True, nullable=False) # 預測的日期
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    
    # 預測的理由或信心分數，未來可擴充
    reason = Column(String, default="高頻率常客") 
    
    student = relationship("Student")

