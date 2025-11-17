from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext

# 設定密碼加密環境
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user_by_phone(db: Session, phone_number: str):
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()

def create_user(db: Session, user: schemas.UserCreate):
    # 密碼加密
    hashed_password = get_password_hash(user.password)
    
    # 建立 User 實例
    db_user = models.User(
        phone_number=user.phone_number,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role
    )
    
    # 存入資料庫
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
