# 檔案路徑: app/crud.py
# 版本：基於新憲法的 v2.0
# 說明：提供了機構、教職員、班級的核心 CRUD 操作。
from fastapi import HTTPException
from typing import List, Optional 
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, security

# ===================================================================
# User / Auth (使用者與認證)
# ===================================================================

def get_user_by_phone(db: Session, phone_number: str) -> Optional[models.User]:
    """
    根據手機號碼獲取使用者。
    關聯的 children (學生) 會在需要時由 SQLAlchemy 自動懶加載。
    """
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()

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


    # vvv--- 家長綁定孩子 ---vvv
def bind_child_to_parent(db: Session, *, parent: models.User, child_info: schemas.ChildBindingCreate) -> models.User:
    """
    將一個學生綁定到指定的家長帳號下，支援最多兩位家長綁定。

    驗證流程:
    1. 尋找學生：確認學生是否存在於指定機構。
    2. 權限驗證：確認請求者提供的手機號，是否與系統為該學生預留的任一家長手機號匹配。
    3. 綁定上限檢查：確認該學生已被綁定的 active 家長數量是否已達上限 (2位)。
    4. 重複綁定檢查：確認當前家長是否已經綁定過此學生。
    5. 執行綁定：將學生添加到家長的 children 列表中。
    """
    # 步驟 1: 尋找學生
    # 我們需要一個新的 crud 函式來完成這件事，我們先假設它存在
    student_to_bind = get_student_by_name_and_institution(
        db, 
        name=child_info.student_full_name, 
        institution_code=child_info.institution_code
    )
    if not student_to_bind:
        raise HTTPException(status_code=404, detail="找不到指定的學生或機構代碼不匹配")

    # 步驟 2: 權限驗證 (手機號驗證)
    # 檢查該學生所有關聯的家長(不論 active 或 invited)
    # 是否有任何一個的手機號與請求者提供的號碼匹配
    can_bind = False
    for associated_parent in student_to_bind.parents:
        if associated_parent.phone_number == child_info.parent_phone_number:
            can_bind = True
            break
    
    if not can_bind:
        raise HTTPException(status_code=403, detail="驗證失敗，您提供的家長手機號與系統預留資訊不符")

    # 步驟 3: 綁定上限檢查
    active_parents_count = sum(1 for p in student_to_bind.parents if p.status == models.UserStatus.active)
    
    if active_parents_count >= 2:
        raise HTTPException(status_code=409, detail="此學生已被綁定，已達人數上限")

    # 步驟 4: 重複綁定檢查
    if student_to_bind in parent.children:
        raise HTTPException(status_code=409, detail="您已經綁定過此學生")

    # 步驟 5: 執行綁定
    parent.children.append(student_to_bind)
    db.add(parent)
    db.commit()
    db.refresh(parent)
    
    return parent

# vvv--- 我們還需要一個輔助函式來查找學生 ---vvv
def get_student_by_name_and_institution(db: Session, name: str, institution_code: str) -> Optional[models.Student]:
    """ 根據學生姓名和機構代碼查找學生 """
    return db.query(models.Student).join(models.Student.class_).join(models.Class.institution).filter(
        models.Student.full_name == name,
        models.Institution.code == institution_code
    ).first()

# ^^^--- 新函式結束 ---^^^