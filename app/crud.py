from sqlalchemy.orm import Session
from . import models, schemas, security

def get_user_by_phone(db: Session, phone_number: str):
    return db.query(models.User).filter(
        models.User.phone_number == phone_number, 
        models.User.is_active == True  # <--- 新增這個過濾條件
    ).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        phone_number=user.phone_number,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
# ... (檔案上方原有的 get_user_by_phone, create_user 函式保持不變) ...

def create_teacher(db: Session, user: schemas.TeacherCreate):
    """
    建立一個具有指定角色的使用者（老師或管理員）。
    """
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        phone_number=user.phone_number,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role  # 使用從請求中傳入的角色
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ... (檔案上方原有的函式保持不變) ...
from . import models

# --- 學生相關 ---
def create_student(db: Session, student: schemas.StudentCreate):
    db_student = models.Student(full_name=student.full_name)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def link_parent_to_student(db: Session, parent_id: int, student_id: int):
    link = models.ParentStudentLink(parent_id=parent_id, student_id=student_id)
    db.add(link)
    db.commit()
    return link

def get_student_by_id(db: Session, student_id: int):
    return db.query(models.Student).filter(
        models.Student.id == student_id,
        models.Student.is_active == True # <--- 新增這個過濾條件
    ).first()

# --- 接送通知相關 ---
def create_pickup_notification(db: Session, parent_id: int, student_id: int):
    # 1. 建立通知紀錄
    db_notification = models.PickupNotification(
        parent_id=parent_id,
        student_id=student_id
    )
    db.add(db_notification)
    
    # 2. 更新學生狀態
    db_student = get_student_by_id(db, student_id=student_id)
    if db_student:
        db_student.status = models.StudentStatus.waiting_pickup
    
    db.commit()
    db.refresh(db_notification)
    return db_notification

# ... (檔案上方原有的函式保持不變) ...

def get_notification_by_id(db: Session, notification_id: int):
    """根據 ID 獲取接送通知。"""
    return db.query(models.PickupNotification).filter(models.PickupNotification.id == notification_id).first()

def complete_pickup_notification(db: Session, notification_id: int):
    """完成一個接送通知。"""
    # 1. 找到該通知
    db_notification = get_notification_by_id(db, notification_id)
    if not db_notification:
        return None

    # 2. 更新通知狀態
    db_notification.status = "completed"
    
    # 3. 更新學生狀態
    db_student = db_notification.student
    if db_student:
        db_student.status = models.StudentStatus.departed
    
    db.commit()
    db.refresh(db_notification)
    
    return db_notification

    # ... (檔案上方原有的函式保持不變) ...

def get_user_by_id(db: Session, user_id: int):
    """一個輔助函式，根據 ID 獲取使用者，不過濾 is_active。"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def deactivate_user(db: Session, user_id: int):
    """邏輯刪除一個使用者。"""
    db_user = get_user_by_id(db, user_id)
    if db_user:
        db_user.is_active = False
        db.commit()
        db.refresh(db_user)
    return db_user

def deactivate_student(db: Session, student_id: int):
    """邏輯刪除一個學生。"""
    db_student = get_student_by_id(db, student_id) # 這裡用的是過濾 active 的版本
    if db_student:
        db_student.is_active = False
        db.commit()
        db.refresh(db_student)
    return db_student

# ... (檔案上方原有的函式保持不變) ...

def update_user_password(db: Session, user_id: int, new_password: str):
    """更新指定使用者的密碼。"""
    db_user = get_user_by_id(db, user_id=user_id)
    if db_user:
        hashed_password = security.get_password_hash(new_password)
        db_user.hashed_password = hashed_password
        db.commit()
        db.refresh(db_user)
    return db_user

