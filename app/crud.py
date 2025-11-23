# 檔案路徑: app/crud.py
# 這是重構的第三步，提供了與新 schemas 完全對應的、清晰的資料庫操作。

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import case, func

from . import models, schemas, security

# ===================================================================
# 使用者 (User) 相關
# ===================================================================

def get_user_by_phone(db: Session, phone_number: str) -> Optional[models.User]:
    """ 根據手機號碼獲取使用者，不過濾狀態。"""
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """ 根據 ID 獲取使用者。"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """ 建立一個具有指定角色的使用者，狀態直接為 active。"""
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        phone_number=user.phone_number,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role,
        status=models.UserStatus.active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def pre_register_parent(db: Session, parent_info: schemas.ParentInvite) -> models.User:
    """
    預註冊一個家長帳號或獲取已存在的家長帳號。
    如果家長不存在，則建立一個 'invited' 狀態的帳號。
    """
    parent = get_user_by_phone(db, phone_number=parent_info.phone_number)
    if not parent:
        parent = models.User(
            phone_number=parent_info.phone_number,
            full_name=parent_info.full_name,
            role=models.UserRole.parent,
            status=models.UserStatus.invited
        )
        db.add(parent)
        db.flush() # 使用 flush 來獲取 parent 的 id，但不結束事務
    return parent

def activate_user_account(db: Session, user: models.User, password: str) -> models.User:
    """ 啟用一個 'invited' 狀態的帳號，設定密碼並更新狀態。"""
    user.hashed_password = security.get_password_hash(password)
    user.status = models.UserStatus.active
    db.commit()
    db.refresh(user)
    return user

# ===================================================================
# 學生 (Student) 相關
# ===================================================================

def get_student(db: Session, student_id: int) -> Optional[models.Student]:
    """ 根據 ID 獲取一個活躍的學生。"""
    return db.query(models.Student).filter(
        models.Student.id == student_id,
        models.Student.is_active == True
    ).first()

def create_student_and_link_parents(
    db: Session, 
    student_data: schemas.StudentCreate,
    teacher_id: int,
    institution_id: int
) -> models.Student:
    """
    交易安全的函式：建立學生，預註冊或關聯家長，並建立綁定關係。
    """
    # 1. 建立學生
    db_student = models.Student(
        full_name=student_data.student_full_name,
        institution_id=institution_id,
        teacher_id=teacher_id
    )
    db.add(db_student)
    db.flush()

    # 2. 處理家長關聯
    if student_data.parents:
        for parent_info in student_data.parents:
            # 預註冊或獲取家長
            parent = pre_register_parent(db, parent_info=parent_info)
            
            # 檢查綁定關係是否已存在
            link = db.query(models.ParentStudentLink).filter_by(parent_id=parent.id, student_id=db_student.id).first()
            if not link:
                db_student.parents.append(parent)
    
    db.commit()
    db.refresh(db_student)
    return db_student

def update_student_status(db: Session, student_id: int, new_status: models.StudentStatus) -> Optional[models.Student]:
    """ 通用的學生狀態更新函式。"""
    db_student = get_student(db, student_id=student_id)
    if db_student:
        db_student.status = new_status
        db.commit()
        db.refresh(db_student)
    return db_student

# ===================================================================
# 接送 (Pickup) 相關
# ===================================================================

def create_pickup_notification(db: Session, parent_id: int, student_id: int) -> models.PickupNotification:
    """ 建立接送通知，並更新學生狀態。"""
    db_notification = models.PickupNotification(parent_id=parent_id, student_id=student_id)
    db.add(db_notification)
    
    db_student = get_student(db, student_id=student_id)
    if db_student:
        db_student.status = models.StudentStatus.parent_is_coming
    
    db.commit()
    db.refresh(db_notification)
    return db_notification

def get_notification(db: Session, notification_id: int) -> Optional[models.PickupNotification]:
    """ 根據 ID 獲取接送通知。"""
    return db.query(models.PickupNotification).filter(models.PickupNotification.id == notification_id).first()

def complete_pickup_notification(db: Session, notification_id: int) -> Optional[models.PickupNotification]:
    """ 完成一個接送通知。"""
    db_notification = get_notification(db, notification_id)
    if not db_notification or db_notification.status != "active":
        return None

    db_notification.status = "completed"
    if db_notification.student:
        db_notification.student.status = models.StudentStatus.departed
    
    db.commit()
    db.refresh(db_notification)
    return db_notification

# ... (其他 CRUD 函式，如 institution, prediction 等可以後續加入)
