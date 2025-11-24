# 檔案路徑: app/crud.py
# 版本：基於新憲法的 v2.0
# 說明：提供了機構、教職員、班級的核心 CRUD 操作。

from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, security

# ===================================================================
# User / Auth (使用者與認證)
# ===================================================================

def get_user_by_phone(db: Session, phone_number: str) -> models.User | None:
    """ 根據手機號碼獲取使用者。"""
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()

# ===================================================================
# Institution (機構)
# ===================================================================

def get_institution_by_code(db: Session, code: str) -> models.Institution | None:
    """ 根據機構代碼查詢機構。"""
    return db.query(models.Institution).filter(models.Institution.code == code).first()

def create_institution(db: Session, institution: schemas.InstitutionCreate) -> models.Institution:
    """ 建立一個新的機構。"""
    db_institution = models.Institution(
        name=institution.name,
        code=institution.code
    )
    db.add(db_institution)
    db.commit()
    db.refresh(db_institution)
    return db_institution

# ===================================================================
# Staff / Admin (教職員與管理)
# ===================================================================

def create_staff_user(db: Session, staff_data: schemas.StaffCreate, institution_id: int) -> models.User:
    """
    在指定機構下，建立一位教職員 (老師/行政/管理員)。
    """
    hashed_password = security.get_password_hash(staff_data.password)
    db_user = models.User(
        phone_number=staff_data.phone_number,
        full_name=staff_data.full_name,
        hashed_password=hashed_password,
        role=staff_data.role,
        status=models.UserStatus.active, # 教職員帳號直接啟用
        institution_id=institution_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_class(db: Session, class_data: schemas.ClassCreate, institution_id: int) -> models.Class:
    """
    在指定機構下，建立一個班級。
    """
    db_class = models.Class(
        name=class_data.name,
        teacher_id=class_data.teacher_id,
        institution_id=institution_id
    )
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class

# ===================================================================
# Parent (家長)
# ===================================================================

def activate_parent_account(db: Session, user: models.User, password: str) -> models.User:
    """
    啟用一個 'invited' 狀態的家長帳號。
    設定其密碼，並將狀態更新為 'active'。
    """
    user.hashed_password = security.get_password_hash(password)
    user.status = models.UserStatus.active
    db.commit()
    db.refresh(user)
    return user

def get_student_by_name_and_institution(db: Session, student_name: str, institution_id: int) -> models.Student | None:
    """ 根據學生姓名和機構ID，查詢活躍的學生。"""
    return db.query(models.Student).join(models.Class).filter(
        models.Student.full_name == student_name,
        models.Class.institution_id == institution_id,
        models.Student.is_active == True
    ).first()

def link_parent_to_student(db: Session, parent_id: int, student_id: int) -> models.ParentStudentLink | None:
    """
    建立家長與學生的綁定關係。
    如果綁定已存在，則不重複建立。
    """
    # 檢查是否已存在完全相同的綁定
    exact_link = db.query(models.ParentStudentLink).filter(
        models.ParentStudentLink.parent_id == parent_id,
        models.ParentStudentLink.student_id == student_id
    ).first()
    
    if not exact_link:
        new_link = models.ParentStudentLink(parent_id=parent_id, student_id=student_id)
        db.add(new_link)
        db.commit()
        return new_link
    return exact_link
