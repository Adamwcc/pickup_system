# 檔案路徑: app/database.py (修改後)

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings # <--- 我們唯一的設定來源

# 1. 直接從 settings 物件獲取資料庫 URL
#    Pydantic 的 BaseSettings 已經幫我們處理了從 .env 或環境變數讀取的邏輯。
#    如果 .env 中沒有定義 DATABASE_URL，Pydantic 會報錯，這比靜默地使用 SQLite 更安全。
#    如果我們依然想保留本地開發的便利性，可以在 config.py 中為 DATABASE_URL 提供一個預設值。
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# 2. 保留對 PostgreSQL URL 的修正邏輯 (這是一個很好的健壯性設計)
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. 根據 URL 的內容，決定 create_engine 的參數
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    # 如果是 SQLite，添加 connect_args
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    # 如果是 PostgreSQL 或其他資料庫，正常創建
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 4. 後續部分保持不變
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
