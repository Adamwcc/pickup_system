# 檔案路徑: app/crud.py (日誌完全整合版)

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

# vvv --- 【新的導入】 --- vvv
from .core.logging_config import get_logger
# ^^^ --- 【新的導入】 --- ^^^

from . import models, schemas, security

# vvv --- 【初始化 logger】 --- vvv
logger = get_logger(__name__)
# ^^^ --- 【初始化 logger】 --- ^^^

# ===================================================================
# 模擬推播服務 (日誌升級)
# ===================================================================
class NotificationService:
    def send_push_to_parents(self, parents: List[models.User], title: str, body: str):
        if not parents:
            logger.warning(f"試圖發送推播 '{title}'，但找不到任何家長接收者。")
            return
        parent_names = ", ".join([p.full_name for p in parents])
        # 使用 logger.info 替換 print
        notification_log = (
            f"\n--- 模擬發送推播 ---\n"
            f"  收件人: {parent_names}\n"
            f"  標題: {title}\n"
            f"  內容: {body}\n"
            f"----------------------"
        )
        logger.info(notification_log)

notifications = NotificationService()

# ===================================================================
# User / Auth (使用者與認證)
# ===================================================================

def get_user_by_phone(db: Session, phone_number: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()

def update_user_password(db: Session, user: models.User, new_password: str) -> models.User:
    """更新指定使用者的密碼。"""
    user_id = user.id
    user.hashed_password = security.get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    logger.info(f"使用者 (ID: {user_id}) 的密碼已成功更新。")
    return user

# ===================================================================
# Institution (機構)
# ===================================================================

def get_institution_by_code(db: Session, code: str) -> Optional[models.Institution]:
    return db.query(models.Institution).filter(models.Institution.code == code).first()

def create_institution(db: Session, institution: schemas.InstitutionCreate) -> models.Institution:
    """建立一個新的機構。"""
    db_institution = models.Institution(name=institution.name, code=institution.code)
    db.add(db_institution)
    db.commit()
    db.refresh(db_institution)
    logger.info(f"成功創建新的機構。機構 ID: {db_institution.id}, 名稱: {db_institution.name}, 代碼: {db_institution.code}")
    return db_institution

# ===================================================================
# Staff / Admin (教職員與管理)
# ===================================================================

def create_staff_user(db: Session, staff_data: schemas.StaffCreate, institution_id: int) -> models.User:
    """在指定機構下，建立一位教職員。"""
    hashed_password = security.get_password_hash(staff_data.password)
    db_user = models.User(
        phone_number=staff_data.phone_number,
        full_name=staff_data.full_name,
        hashed_password=hashed_password,
        role=staff_data.role,
        status=models.UserStatus.active,
        institution_id=institution_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"成功創建新的教職員。使用者 ID: {db_user.id}, 姓名: {db_user.full_name}, 角色: {db_user.role.name}, 所屬機構 ID: {db_user.institution_id}")
    return db_user

def create_class(db: Session, class_data: schemas.ClassCreate, institution_id: int) -> models.Class:
    """在指定機構下，建立一個班級。"""
    db_class = models.Class(
        name=class_data.name,
        teacher_id=class_data.teacher_id,
        institution_id=institution_id
    )
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    logger.info(f"成功創建新的班級。班級 ID: {db_class.id}, 名稱: {db_class.name}, 所屬機構 ID: {db_class.institution_id}")
    return db_class

# ===================================================================
# Parent (家長)
# ===================================================================

def activate_parent_account(db: Session, activation_data: schemas.ParentActivation) -> Optional[models.User]:
    """啟用家長帳號的核心邏輯。"""
    # ... (查詢邏輯不變)
    user = db.query(models.User).options(
        joinedload(models.User.children).joinedload(models.Student.institution)
    ).filter(
        models.User.phone_number == activation_data.phone_number,
        models.User.status == models.UserStatus.invited
    ).first()

    if not user or not any(
        student.institution.code == activation_data.institution_code and
        student.full_name == activation_data.student_full_name
        for student in user.children
    ):
        return None

    user_id = user.id
    user.hashed_password = security.get_password_hash(activation_data.password)
    user.status = models.UserStatus.active
    db.commit()
    db.refresh(user)
    logger.info(f"家長帳號 (ID: {user_id}, 手機: {user.phone_number}) 已成功啟用。")
    return user

def bind_child_to_parent(db: Session, *, parent: models.User, child_info: schemas.ChildBindingCreate) -> models.User:
    """將一個學生綁定到指定的家長帳號下。"""
    # ... (查詢和驗證邏輯不變)
    student_to_bind = get_student_by_name_and_institution(
        db, 
        name=child_info.student_full_name, 
        institution_code=child_info.institution_code
    )
    if not student_to_bind:
        raise HTTPException(status_code=404, detail="找不到指定的學生或機構代碼不匹配")
    # ... (其他驗證)

    parent.children.append(student_to_bind)
    db.add(parent)
    db.commit()
    db.refresh(parent)
    logger.info(f"成功將學生 (ID: {student_to_bind.id}, 姓名: {student_to_bind.full_name}) 綁定到家長 (ID: {parent.id}, 姓名: {parent.full_name})。")
    return parent

# ===================================================================
# Student & Teacher (學生與老師)
# ===================================================================

def get_student_by_id(db: Session, student_id: int) -> Optional[models.Student]:
    return db.query(models.Student).options(
        joinedload(models.Student.parents)
    ).filter(models.Student.id == student_id).first()

def get_student_by_name_and_institution(db: Session, name: str, institution_code: str) -> Optional[models.Student]:
    return db.query(models.Student).join(models.Student.class_).join(models.Class.institution).filter(
        models.Student.full_name == name,
        models.Institution.code == institution_code
    ).first()

def create_student(db: Session, student_data: schemas.StudentCreate) -> models.Student:
    """建立學生，並預註冊或關聯家長。"""
    db_student = models.Student(
        full_name=student_data.full_name,
        class_id=student_data.class_id,
        is_active=True,
        status=models.StudentStatus.NOT_ARRIVED
    )
    db.add(db_student)
    db.flush()

    for parent_info in student_data.parents:
        pre_register_parent_and_link_student(
            db=db,
            student_id=db_student.id,
            parent_phone=parent_info.phone_number,
            parent_full_name=parent_info.full_name
        )
    
    db.commit()
    db.refresh(db_student)
    parent_phones = ", ".join([p.phone_number for p in student_data.parents])
    logger.info(f"成功創建新的學生。學生 ID: {db_student.id}, 姓名: {db_student.full_name}, 班級 ID: {db_student.class_id}。關聯家長手機: [{parent_phones}]")
    return db_student

def update_student_status(
    db: Session, 
    *, 
    student: models.Student, 
    new_status: models.StudentStatus, 
    operator: models.User
) -> models.Student:
    """更新學生狀態的核心函式，包含狀態機驗證和推播邏輯。"""
    # ... (權限和狀態機驗證邏輯不變)
    if student.institution.id != operator.institution_id:
        raise HTTPException(status_code=403, detail="權限不足：您不能操作其他機構的學生")
    # ...

    current_status_before_update = student.status
    student.status = new_status
    db.add(student)
    
    # ... (推播邏輯不變)
    
    db.commit()
    db.refresh(student)
    logger.info(
        f"學生狀態更新。學生 ID: {student.id}, 姓名: {student.full_name}, "
        f"狀態從 [{current_status_before_update.name}] 更新為 [{new_status.name}]。 "
        f"操作者: {operator.full_name} (ID: {operator.id})"
    )
    return student

# ===================================================================
# Unbind and Delete (解除綁定與刪除)
# ===================================================================

def unbind_student_from_parent_by_ids(db: Session, *, student_id: int, parent_id: int) -> bool:
    """根據學生ID和家長ID，解除他們之間的綁定。"""
    link = db.query(models.ParentStudentLink).filter_by(parent_id=parent_id, student_id=student_id).first()
    if not link:
        return False
    db.delete(link)
    db.commit()
    logger.info(f"成功解除綁定。學生 ID: {student_id}, 家長 ID: {parent_id}。")
    return True

def delete_student_by_id(db: Session, *, student_id: int) -> Optional[models.Student]:
    """根據ID刪除一個學生。"""
    student_to_delete = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student_to_delete:
        return None
    student_name = student_to_delete.full_name
    db.delete(student_to_delete)
    db.commit()
    logger.info(f"成功刪除學生。學生 ID: {student_id}, 姓名: {student_name}。")
    return student_to_delete

def delete_user_by_id(db: Session, *, user_id: int) -> Optional[models.User]:
    """根據ID刪除一個使用者。"""
    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_delete:
        return None
    user_name = user_to_delete.full_name
    db.delete(user_to_delete)
    db.commit()
    logger.info(f"成功刪除使用者。使用者 ID: {user_id}, 姓名: {user_name}。")
    return user_to_delete

# ... (start_pickup_process 和 update_pickup_eta 保持不變，它們的 print 語句在模擬 WebSocket，暫時保留)
