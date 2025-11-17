from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os # 匯入 os 模組

# 從環境變數中讀取資料庫 URL
# 如果找不到，就繼續使用 SQLite (方便本地開發)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./school_pickup.db")

# 如果是 PostgreSQL URL，SQLAlchemy 1.4+ 需要將 postgres:// 改為 postgresql://
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 如果是 SQLite，需要額外的 connect_args
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
