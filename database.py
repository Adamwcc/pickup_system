from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 從環境變數讀取資料庫連線 URL
# DATABASE_URL = os.getenv("DATABASE_URL")
# 為了在 Manus Agent 環境中直接執行，我們暫時硬編碼 URL
DATABASE_URL = "postgresql://pickup_db_8zoh_user:v89YAAUBFocF3f6t034IRzQZvDiPA9IY@dpg-d4dboufdiees73cggc10-a/pickup_db_8zoh"

# 建立 SQLAlchemy 引擎
engine = create_engine(DATABASE_URL)

# 建立一個 SessionLocal 類別，用於資料庫會話
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立一個 Base 類別，我們的 ORM 模型將繼承它
Base = declarative_base()
