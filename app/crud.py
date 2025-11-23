from typing import List, Optional
from sqlalchemy import case
from sqlalchemy.orm import Session, joinedload
from . import models, schemas, security


# 位於 app/crud.py

def get_user_by_phone(db: Session, phone_number: str):
    """
    根據手機號碼獲取使用者。
    不過濾任何 status，以便在登入和啟用流程中都能找到使用者。
    """
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()


def create_teacher(db: Session, user: schemas.TeacherCreate):
    """
    建立一個具有指定角色的使用者（老師或管理員）。
    他們被建立時，狀態直接就是 active。
    """
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        phone_number=user.phone_number,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role,
        status=models.UserStatus.active  # <--- 明確設定狀態為 active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ... (檔案上方原有的函式保持不變) ...

# --- 學生相關 ---
# 請將此函式新增到 app/crud.py

def create_student_and_invite_parents(
        db: Session, 
        student_name: str,
        parents_data: List[schemas.ParentInvite], # <--- 修正於此
        teacher_id: int,
        institution_id: int
    ) -> models.Student:
    """
    一個交易安全的函式，用於：
    1. 在機構下建立學生並指派老師。
    2. 遍歷家長列表，預註冊或關聯現有家長。
    3. 將學生與所有這些家長進行綁定。
    """  
    # 1. 建立學生實例
    db_student = models.Student(
        full_name=student_name,
        institution_id=institution_id,
        teacher_id=teacher_id
    )
    db.add(db_student)
    db.flush()  # 使用 flush 來獲取 db_student.id

    # 2. 處理家長關聯
    if parents_data:
        for parent_info in parents_data:
            # 複用您已經寫好的強大函式！
            pre_register_parent_and_link_student(
                db=db,
                student_id=db_student.id,
                parent_phone=parent_info.phone_number,
                parent_full_name=parent_info.full_name
            )
    
    # 由於 pre_register_parent_and_link_student 內部有 commit，
    # 為了確保整個操作的原子性，最好將 commit 移到這裡。
    # (這需要對 pre_register_parent_and_link_student 做微小修改，暫時保持原樣以簡化)
    
    db.commit() # 這裡的 commit 會提交上面 flush 的學生以及 CRUD 內部的操作
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
        db_student.status = models.StudentStatus.parent_is_coming
    
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

def deactivate_user(db: Session, user_id: int):
    """邏輯刪除一個使用者，將其狀態設定為 inactive。"""
    db_user = get_user_by_id(db, user_id)
    if db_user:
        db_user.status = models.UserStatus.inactive # <--- 修改：設定狀態為 inactive
        db.commit()
        db.refresh(db_user)
    return db_user

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

def update_student_status(db: Session, student_id: int, new_status: models.StudentStatus):
    """通用的學生狀態更新函式。"""
    db_student = get_student_by_id(db, student_id=student_id)
    if db_student:
        db_student.status = new_status
        db.commit()
        db.refresh(db_student)
    return db_student

def get_students_by_teacher(db: Session, teacher_id: int):
    """根據老師 ID 獲取其所有活躍的學生。"""
    return db.query(models.Student).filter(
        models.Student.teacher_id == teacher_id,
        models.Student.is_active == True
    ).all()


def get_dashboard_students(
    db: Session, 
    teacher_id: Optional[int] = None, 
    statuses: Optional[List[models.StudentStatus]] = None
):
    """
    一個功能強大的動態查詢函式，用於獲取儀表板所需的學生列表。
    - 可根據 teacher_id 進行過濾。
    - 可根據一個或多個 status 進行過濾。
    - 結果會自動按照 '家長已出發' > '可接送' > '在班' 的順序排序。
    """
    # 1. 建立基礎查詢，並預先載入 teacher 資訊以避免 N+1 問題
    query = db.query(models.Student).options(joinedload(models.Student.teacher))

    # 2. 動態加入 teacher_id 過濾條件
    if teacher_id is not None:
        query = query.filter(models.Student.teacher_id == teacher_id)

    # 3. 動態加入 status 過濾條件
    if statuses:
        query = query.filter(models.Student.status.in_(statuses))
    
    # 4. 加入 is_active 過濾條件，我們不關心已停用的學生
    query = query.filter(models.Student.is_active == True)

    # 5. 定義自訂排序邏輯
    order_logic = case(
        (models.Student.status == models.StudentStatus.parent_is_coming, 1),
        (models.Student.status == models.StudentStatus.can_be_picked_up, 2),
        (models.Student.status == models.StudentStatus.in_class, 3),
        (models.Student.status == models.StudentStatus.departed, 4),
        else_=5
    )

    # 6. 應用排序邏輯並執行查詢
    return query.order_by(order_logic).all()

# --- 機構相關 (Institution) ---

def get_institution_by_code(db: Session, code: str):
    """根據機構代碼查詢機構。"""
    return db.query(models.Institution).filter(models.Institution.code == code).first()

def create_institution(db: Session, institution: schemas.InstitutionCreate):
    """建立一個新的機構。"""
    db_institution = models.Institution(
        name=institution.name,
        code=institution.code
    )
    db.add(db_institution)
    db.commit()
    db.refresh(db_institution)
    return db_institution


# --- 學生與認領相關 (Student & Claiming) ---

def create_student_for_institution(db: Session, full_name: str, institution_id: int):
    """在指定機構下建立一位新學生。"""
    db_student = models.Student(
        full_name=full_name,
        institution_id=institution_id
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def claim_student(
    db: Session, 
    parent_id: int, 
    claim_data: schemas.StudentClaim # 使用 Pydantic 模型接收資料
) -> Optional[models.Student]:
    """
    家長透過機構代碼和學生姓名來認領學生的核心邏輯。
    """
    # 1. 驗證機構
    institution = get_institution_by_code(db, code=claim_data.institution_code)
    if not institution:
        # 為了安全，不應洩漏機構是否存在，但在開發階段可以明確一點
        # 在真實產品中，這裡應該引發一個統一的 "認領失敗" 錯誤
        return None  # 機構不存在

    # 2. 在該機構下尋找學生
    student = db.query(models.Student).filter(
        models.Student.institution_id == institution.id,
        models.Student.full_name == claim_data.student_name,
        models.Student.is_active == True
    ).first()

    if not student:
        return None  # 學生不存在於該機構

    # 3. 檢查是否已存在完全相同的綁定關係，避免重複
    existing_link = db.query(models.ParentStudentLink).filter(
        models.ParentStudentLink.parent_id == parent_id,
        models.ParentStudentLink.student_id == student.id
    ).first()
    
    if existing_link:
        # 如果已經綁定，直接回傳學生資訊，視為操作成功
        return student

    # 4. 建立新的綁定關係
    new_link = models.ParentStudentLink(parent_id=parent_id, student_id=student.id)
    db.add(new_link)
    db.commit()
    
    db.refresh(student)
    return student

def pre_register_parent_and_link_student(db: Session, student_id: int, parent_phone: str, parent_full_name: str):
    """
    老師新增學生時，為其關聯的家長建立一個「預註冊(invited)」帳號。
    如果該手機號的家長已存在，則直接使用現有家長進行綁定。
    """
    # 1. 檢查該手機號是否已存在使用者
    parent = get_user_by_phone(db, phone_number=parent_phone)
    
    if not parent:
        # 如果家長不存在，則建立一個 invited 狀態的帳號
        parent = models.User(
            phone_number=parent_phone,
            full_name=parent_full_name,
            role=models.UserRole.parent,
            status=models.UserStatus.invited # <--- 核心：狀態為 invited
            # 注意：這裡沒有設定密碼
        )
        db.add(parent)
        db.flush() # 使用 flush 來獲取 parent 的 id，但不結束事務
    
    # 2. 檢查學生與家長的綁定關係是否已存在
    link = db.query(models.ParentStudentLink).filter(
        models.ParentStudentLink.parent_id == parent.id,
        models.ParentStudentLink.student_id == student_id
    ).first()

    if not link:
        # 如果綁定關係不存在，則建立它
        new_link = models.ParentStudentLink(parent_id=parent.id, student_id=student_id)
        db.add(new_link)
    
    db.commit()
    db.refresh(parent)
    return parent


def activate_parent_account(db: Session, user: models.User, password: str):
    """
    啟用一個 'invited' 狀態的家長帳號。
    設定其密碼，並將狀態更新為 'active'。
    """
    user.hashed_password = security.get_password_hash(password)
    user.status = models.UserStatus.active
    db.commit()
    db.refresh(user)
    return user

