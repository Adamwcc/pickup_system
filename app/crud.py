# 檔案路徑: app/crud.py
# 版本：基於新憲法的 v2.0
# 說明：提供了機構、教職員、班級的核心 CRUD 操作。
from typing import List, Optional 
from sqlalchemy.orm import Session, joinedload
from typing import List

from . import models, schemas, security

# ===================================================================
# User / Auth (使用者與認證)
# ===================================================================

def get_user_by_phone(db: Session, phone_number: str) -> Optional[models.User]:
    """
    根據手機號碼獲取使用者，並預先載入所有相關的學生和機構資訊。
    這是為了在後續的驗證流程中，避免額外的資料庫查詢 (N+1 問題)。
    """
    return db.query(models.User).options(
        # 當載入 user.children 時，
        # 對於每一個 child (student)，都立刻 join 並載入其 institution 屬性。
        joinedload(models.User.children).joinedload(models.Student.institution)
    ).filter(models.User.phone_number == phone_number).first()

def update_user_password(db: Session, user: models.User, new_password: str) -> models.User:
    """ 更新指定使用者的密碼。"""
    user.hashed_password = security.get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user

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

def activate_parent_account(db: Session, activation_data: schemas.ParentActivation) -> Optional[models.User]:
    """
    啟用家長帳號的核心邏輯。
    1. 驗證手機號是否存在，且狀態為 'invited'。
    2. 驗證該家長是否確實與所提供的 '機構代碼' 和 '學生姓名' 的孩子相關聯。
    3. 如果全部通過，則設定密碼，並將狀態更新為 'active'。
    """
    # 1. 尋找處於 'invited' 狀態的使用者
    user = db.query(models.User).filter(
        models.User.phone_number == activation_data.phone_number,
        models.User.status == models.UserStatus.invited
    ).first()

    if not user:
        return None  # 找不到符合條件的待啟用帳號

    # 2. 驗證身份：檢查該使用者是否關聯了指定學生
    student_found = False
    for student in user.children:
        if (student.institution.code == activation_data.institution_code and
            student.full_name == activation_data.student_full_name):
            student_found = True
            break
    
    if not student_found:
        return None # 提供的學生資訊不匹配

    # 3. 更新使用者資訊
    user.hashed_password = security.get_password_hash(activation_data.password)
    user.status = models.UserStatus.active
    db.commit()
    db.refresh(user)
    
    return user

# ===================================================================
# Student & Teacher (學生與老師)
# ===================================================================

def pre_register_parent_and_link_student(db: Session, student_id: int, parent_phone: str, parent_full_name: Optional[str] = None) -> models.User:
    """
    老師新增學生時，為其關聯的家長建立一個「預註冊(invited)」帳號。
    如果該手機號的家長已存在，則直接使用現有家長進行綁定。
    """
    parent = get_user_by_phone(db, phone_number=parent_phone)
    
    if not parent:
        parent = models.User(
            phone_number=parent_phone,
            # 如果 full_name 是 None，就用手機號作為預設名
            full_name=parent_full_name if parent_full_name is not None else parent_phone,
            role=models.UserRole.parent,
            status=models.UserStatus.invited
        )
        db.add(parent)
    
    db.flush()
    link_parent_to_student(db, parent_id=parent.id, student_id=student_id)
    
    return parent

# vvv--- 同時也替換這個函式 ---vvv
def create_student(db: Session, student_data: schemas.StudentCreate, operator_id: int) -> models.Student:
    """
    一個交易安全的函式，用於：
    1. 在機構和班級下建立學生。
    2. 遍歷家長列表，預註冊或關聯現有家長。
    """
    db_student = models.Student(
        full_name=student_data.full_name,
        class_id=student_data.class_id,
        is_active=True,
        status=models.StudentStatus.departed
    )
    db.add(db_student)
    db.flush()

    if student_data.parents:
        for parent_info in student_data.parents:
            pre_register_parent_and_link_student(
                db=db,
                student_id=db_student.id,
                parent_phone=parent_info.phone_number,
                # 直接傳遞可能為 None 的 full_name
                parent_full_name=parent_info.full_name 
            )
    
    db.commit()
    db.refresh(db_student)
    return db_student