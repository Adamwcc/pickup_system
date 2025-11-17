from sqlalchemy.orm import Session
from . import models, schemas, security

def get_user_by_phone(db: Session, phone_number: str):
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()

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
    return db.query(models.Student).filter(models.Student.id == student_id).first()

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
