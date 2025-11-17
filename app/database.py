from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite 資料庫檔案的路徑
SQLALCHEMY_DATABASE_URL = "sqlite:///./school_pickup.db"

# 建立資料庫引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 建立資料庫 Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立一個 Base 類，我們的 ORM 模型將繼承它
Base = declarative_base()
