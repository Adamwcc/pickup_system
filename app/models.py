# 檔案路徑: app/models.py
# 這是基於新憲法的第一步，建立了支援精細化權限和班級的資料庫模型。

from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy

from .database import Base
import enum
from datetime import datetime

# ===================================================================
# Enums (列舉) - 定義系統中所有可選的狀態和角色
# ===================================================================

class UserRole(str, enum.Enum):
    """ 使用者角色 """
    parent = "parent"
    teacher = "teacher"          # 帶班老師
    receptionist = "receptionist"  # 行政老師
    admin = "admin"              # 機構管理員
    super_admin = "super_admin"  # (未來預留) 平台超級管理員

class UserStatus(str, enum.Enum):
    """ 使用者帳號狀態 """
    invited = "invited"      # 已被邀請，但尚未啟用
    active = "active"        # 已啟用，正常使用
    inactive = "inactive"    # 已停用/邏輯刪除

class StudentStatus(str, enum.Enum):
    """ 
    學生狀態 (每日會被重置) - v2.0
    定義了學生在安親班一天的完整生命週期。
    """
    # 【新狀態】每日 00:00 自動重置為此狀態
    NOT_ARRIVED = "未進班"
    # 老師點名後
    ARRIVED = "已進班"
    # 學生完成作業後
    READY_FOR_PICKUP = "可以接送"
    # 學生需要更多時間
    HOMEWORK_PENDING = "作業未完成"
    # 家長發起接送後
    PARENT_EN_ROUTE = "家長已出發"
    # 【新狀態】老師確認學生被接走後
    PICKUP_COMPLETED = "完成接送"

# ===================================================================
# 主要模型 (Primary Models)
# ===================================================================

class Institution(Base):
    """ 機構模型 """
    __tablename__ = "institutions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)

    # 反向關聯
    staff = relationship("User", back_populates="institution")
    classes = relationship("Class", back_populates="institution")

class User(Base):
    """ 使用者模型 (包含家長、老師、管理員) """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True) # invited 狀態的家長可以沒有密碼
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.active, nullable=False)
    
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True) # 家長在啟用前可能沒有機構
    
    # 關聯
    institution = relationship("Institution", back_populates="staff")
    # 作為家長，關聯的孩子
    children = relationship("Student", secondary="parent_student_link", back_populates="parents")
    # 作為帶班老師，關聯的班級
    teaching_class = relationship("Class", back_populates="teacher", uselist=False) # 一個老師只帶一個班

class Class(Base):
    """ 班級模型 """
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True) # 班級可以暫時沒有老師
    
    # 關聯
    institution = relationship("Institution", back_populates="classes")
    teacher = relationship("User", back_populates="teaching_class")
    students = relationship("Student", back_populates="class_") # class 是關鍵字，用 class_

class Student(Base):
    """ 學生模型 """
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True, nullable=False)
    status = Column(Enum(StudentStatus), default=models.StudentStatus.NOT_ARRIVED.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    
    # 關聯
    class_ = relationship("Class", back_populates="students")
    
    # vvv--- 用下面這行 association_proxy，替換掉舊的 institution = relationship(...) ---vvv
    institution = association_proxy("class_", "institution")
    # ^^^--- 替換結束 ---^^^
    
    parents = relationship("User", secondary="parent_student_link", back_populates="children")
    notifications = relationship("PickupNotification", back_populates="student")
    
# ===================================================================
# 中間表與附屬模型
# ===================================================================

class ParentStudentLink(Base):
    """ 家長-學生 多對多關聯表 """
    __tablename__ = "parent_student_link"
    parent_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), primary_key=True)

class PickupNotification(Base):
    """ 接送通知記錄 """
    __tablename__ = "pickup_notifications"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active") # active, completed, cancelled
    
    student = relationship("Student", back_populates="notifications")
    parent = relationship("User")

# (PickupPrediction 模型暫時保持不變，我們可以在後續階段再優化它)
class PickupPrediction(Base):
    __tablename__ = "pickup_predictions"
    id = Column(Integer, primary_key=True, index=True)
    prediction_date = Column(DateTime, index=True, nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    reason = Column(String, default="高頻率常客")
    student = relationship("Student")
