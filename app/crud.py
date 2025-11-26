# 檔案路徑: app/crud.py
# 版本：v2.1 - 新增 update_student_status 核心函式

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from . import models, schemas, security

# ===================================================================
# 模擬推播服務 (Placeholder for Notification Service)
# ===================================================================

# 在真實的應用中，這會是一個與 Firebase, APNS 等服務對接的複雜模組。
# 現在，我們只用一個簡單的類別和 print 語句來模擬它。
class NotificationService:
    def send_push_to_parents(self, parents: List[models.User], title: str, body: str):
        parent_names = ", ".join([p.full_name for p in parents])
        print(f"--- SENDING PUSH to [{parent_names}] ---")
        print(f"  Title: {title}")
        print(f"  Body: {body}")
        print(f"------------------------------------")

notifications = NotificationService() # 創建一個全域實例

# ===================================================================
# User / Auth (使用者與認證)
# ===================================================================

def get_user_by_phone(db: Session, phone_number: str) -> Optional[models.User]:
    """根據手機號碼獲取使用者。"""
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()

def update_user_password(db: Session, user: models.User, new_password: str) -> models.User:
    """更新指定使用者的密碼。"""
    user.hashed_password = security.get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user

# ===================================================================
# Institution (機構)
# ===================================================================

def get_institution_by_code(db: Session, code: str) -> Optional[models.Institution]:
    """根據機構代碼查詢機構。"""
    return db.query(models.Institution).filter(models.Institution.code == code).first()

def create_institution(db: Session, institution: schemas.InstitutionCreate) -> models.Institution:
    """建立一個新的機構。"""
    db_institution = models.Institution(name=institution.name, code=institution.code)
    db.add(db_institution)
    db.commit()
    db.refresh(db_institution)
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
    return db_class

# ===================================================================
# Parent (家長)
# ===================================================================

def activate_parent_account(db: Session, activation_data: schemas.ParentActivation) -> Optional[models.User]:
    """啟用家長帳號的核心邏輯。"""
    user = db.query(models.User).options(
        joinedload(models.User.children).joinedload(models.Student.institution)
    ).filter(
        models.User.phone_number == activation_data.phone_number,
        models.User.status == models.UserStatus.invited
    ).first()

    if not user:
        return None

    student_found = any(
        student.institution.code == activation_data.institution_code and
        student.full_name == activation_data.student_full_name
        for student in user.children
    )
    
    if not student_found:
        return None

    user.hashed_password = security.get_password_hash(activation_data.password)
    user.status = models.UserStatus.active
    db.commit()
    db.refresh(user)
    return user

def bind_child_to_parent(db: Session, *, parent: models.User, child_info: schemas.ChildBindingCreate) -> models.User:
    """將一個學生綁定到指定的家長帳號下。"""
    student_to_bind = get_student_by_name_and_institution(
        db, 
        name=child_info.student_full_name, 
        institution_code=child_info.institution_code
    )
    if not student_to_bind:
        raise HTTPException(status_code=404, detail="找不到指定的學生或機構代碼不匹配")

    can_bind = any(
        p.phone_number == child_info.parent_phone_number 
        for p in student_to_bind.parents
    )
    if not can_bind:
        raise HTTPException(status_code=403, detail="驗證失敗，您提供的家長手機號與系統預留資訊不符")

    active_parents_count = sum(1 for p in student_to_bind.parents if p.status == models.UserStatus.active)
    if active_parents_count >= 2:
        raise HTTPException(status_code=409, detail="此學生已被綁定，已達人數上限")

    if student_to_bind in parent.children:
        raise HTTPException(status_code=409, detail="您已經綁定過此學生")

    parent.children.append(student_to_bind)
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent

# ===================================================================
# Student & Teacher (學生與老師)
# ===================================================================

def get_student_by_id(db: Session, student_id: int) -> Optional[models.Student]:
    """根據 ID 獲取學生，並預加載其家長資訊。"""
    return db.query(models.Student).options(
        joinedload(models.Student.parents)
    ).filter(models.Student.id == student_id).first()

def get_student_by_name_and_institution(db: Session, name: str, institution_code: str) -> Optional[models.Student]:
    """根據學生姓名和機構代碼查找學生。"""
    return db.query(models.Student).join(models.Student.class_).join(models.Class.institution).filter(
        models.Student.full_name == name,
        models.Institution.code == institution_code
    ).first()

def pre_register_parent_and_link_student(db: Session, student_id: int, parent_phone: str, parent_full_name: Optional[str] = None):
    """為學生關聯的家長建立一個「預註冊(invited)」帳號。"""
    parent = get_user_by_phone(db, phone_number=parent_phone)
    if not parent:
        parent = models.User(
            phone_number=parent_phone,
            full_name=parent_full_name or parent_phone,
            role=models.UserRole.parent,
            status=models.UserStatus.invited
        )
        db.add(parent)
        db.flush() # 確保 parent 獲得 ID
    
    # 檢查綁定是否已存在
    link = db.query(models.ParentStudentLink).filter_by(parent_id=parent.id, student_id=student_id).first()
    if not link:
        new_link = models.ParentStudentLink(parent_id=parent.id, student_id=student_id)
        db.add(new_link)

def create_student(db: Session, student_data: schemas.StudentCreate) -> models.Student:
    """建立學生，並預註冊或關聯家長。"""
    # 【Bug修復】確保新學生的狀態是我們新的預設值
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
    return db_student

# vvv--- 【新函式】這就是我們第七階段的心臟 ---vvv
def update_student_status(
    db: Session, 
    *, 
    student: models.Student, 
    new_status: models.StudentStatus, 
    operator: models.User
) -> models.Student:
    """
    更新學生狀態的核心函式，包含狀態機驗證和推播邏輯。
    """
    # 權限檢查：確保操作者與學生在同一個機構
    if student.institution.id != operator.institution_id:
        raise HTTPException(status_code=403, detail="權限不足：您不能操作其他機構的學生")

    current_status = student.status
    
    # 狀態機合法性驗證 (v2.0 規則)
    valid_transitions = {
        models.StudentStatus.NOT_ARRIVED: [models.StudentStatus.ARRIVED],
        models.StudentStatus.ARRIVED: [models.StudentStatus.READY_FOR_PICKUP, models.StudentStatus.HOMEWORK_PENDING, models.StudentStatus.PICKUP_COMPLETED],
        models.StudentStatus.HOMEWORK_PENDING: [models.StudentStatus.READY_FOR_PICKUP],
        models.StudentStatus.READY_FOR_PICKUP: [models.StudentStatus.PICKUP_COMPLETED],
        models.StudentStatus.PARENT_EN_ROUTE: [models.StudentStatus.PICKUP_COMPLETED],
        # PICKUP_COMPLETED 是終態，不能轉換到其他狀態 (直到每日重置)
    }

    # 允許從任何狀態（除了終態）被老師手動標記為接走
    if new_status == models.StudentStatus.PICKUP_COMPLETED and current_status != models.StudentStatus.PICKUP_COMPLETED:
        pass # 允許轉換
    elif new_status not in valid_transitions.get(current_status, []):
        raise HTTPException(
            status_code=409, 
            detail=f"狀態轉換無效：無法從 '{current_status.value}' 轉換到 '{new_status.value}'"
        )

    # 更新狀態
    student.status = new_status
    db.add(student)
    
    # --- 推播邏輯 (Push Notification Logic) ---
    if new_status == models.StudentStatus.ARRIVED:
        notifications.send_push_to_parents(
            parents=student.parents,
            title="寶貝已安全抵達",
            body=f"{student.full_name} 已於現在安全抵達安親班。"
        )
    elif new_status == models.StudentStatus.READY_FOR_PICKUP:
        notifications.send_push_to_parents(
            parents=student.parents,
            title="可以準備接寶貝回家囉！",
            body=f"{student.full_name} 已完成今日進度，可以準備接送了！"
        )
    elif new_status == models.StudentStatus.HOMEWORK_PENDING:
        notifications.send_push_to_parents(
            parents=student.parents,
            title="作業進度提醒",
            body=f"{student.full_name} 今日作業較多，可能需要延後接送，請您出發前確認。"
        )
    
    db.commit()
    db.refresh(student)
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
    return True

def delete_student_by_id(db: Session, *, student_id: int) -> Optional[models.Student]:
    """根據ID刪除一個學生。"""
    student_to_delete = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student_to_delete:
        return None
    db.delete(student_to_delete)
    db.commit()
    return student_to_delete

def delete_user_by_id(db: Session, *, user_id: int) -> Optional[models.User]:
    """根據ID刪除一個使用者。"""
    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_delete:
        return None
    db.delete(user_to_delete)
    db.commit()
    return user_to_delete


# vvv---接送發起邏輯---vvv
def start_pickup_process(
    db: Session, 
    *, 
    student: models.Student, 
    parent: models.User
) -> models.Student:
    """
    由家長發起接送流程。
    1. 驗證家長與學生的綁定關係。
    2. 驗證學生的狀態是否允許發起接送。
    3. 更新學生狀態為 PARENT_EN_ROUTE。
    4. 創建 PickupNotification 記錄。
    5. 【未來】觸發 WebSocket 廣播。
    """
    # 步驟 1: 驗證綁定關係
    if student not in parent.children:
        raise HTTPException(status_code=403, detail="權限不足：您未綁定此學生")

    # 步驟 2: 驗證狀態
    allowed_statuses = [
        models.StudentStatus.ARRIVED,
        models.StudentStatus.READY_FOR_PICKUP,
        models.StudentStatus.HOMEWORK_PENDING
    ]
    if student.status not in allowed_statuses:
        raise HTTPException(status_code=409, detail=f"操作無效：學生當前狀態為 '{student.status.value}'，無法發起接送")

    # 步驟 3: 更新學生狀態
    student.status = models.StudentStatus.PARENT_EN_ROUTE
    db.add(student)

    # 步驟 4: 創建通知記錄
    notification = models.PickupNotification(
        student_id=student.id,
        parent_id=parent.id,
        # status 欄位可以更詳細，但現在用預設值即可
    )
    db.add(notification)

    # 步驟 5: 【未來】觸發 WebSocket 廣播
    # 在 websocket.py 完善後，我們會在這裡呼叫它
    # websocket_manager.broadcast_to_institution(
    #     institution_id=student.institution.id,
    #     message={"type": "PICKUP_STARTED", "student_name": student.full_name, "parent_name": parent.full_name}
    # )
    print(f"--- WEBSOCKET BROADCAST to institution [{student.institution.id}] ---")
    print(f"  Message: {student.full_name} 的家長 {parent.full_name} 已出發接送！")
    print(f"-----------------------------------------------------------------")


    db.commit()
    db.refresh(student)
    return student

def update_pickup_eta(
    db: Session, 
    *, 
    student: models.Student, 
    parent: models.User, 
    minutes_remaining: int
) -> None:
    """
    由家長端 App 呼叫，用於廣播 ETA 更新。
    這是一個輕量級操作，只觸發廣播，不寫入資料庫。
    """
    if student not in parent.children:
        raise HTTPException(status_code=403, detail="權限不足：您未綁定此學生")

    # 【未來】觸發 WebSocket 廣播
    # vvv--- 【修正】刪除這一行前面的星號 '*' ---vvv
    # websocket_manager.broadcast_to_institution(
    #     institution_id=student.institution.id,
    #     message={"type": "ETA_UPDATE", "student_name": student.full_name, "minutes_remaining": minutes_remaining}
    # )
    # ^^^--- 修正結束 ---^^^
    
    print(f"--- WEBSOCKET BROADCAST to institution [{student.institution.id}] ---")
    print(f"  Message: {student.full_name} 的家長預計還有 {minutes_remaining} 分鐘到達！")
    print(f"-----------------------------------------------------------------")
    
    return

