# 檔案路徑: scripts/daily_reset.py
# 職責: 在每日午夜，將所有學生的狀態重置為 'NOT_ARRIVED'。

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# --- 步驟 1: 將專案根目錄添加到 Python 路徑中 ---
# 這一步至關重要，它確保了腳本可以找到 app 模組中的內容。
# 我們假設這個腳本位於 pickup_system/scripts/ 目錄下。
# 我們需要將 pickup_system 這個根目錄，添加到 sys.path 中。
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(ROOT_DIR)

# 現在，我們可以安全地從 app 模組導入了
from app.models import StudentStatus

# --- 步驟 2: 加載環境變數 ---
# 我們將從 .env 檔案中讀取資料庫的 URL。
# 確保您的專案根目錄 (pickup_system/) 下，有一個 .env 檔案。
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("錯誤：找不到 DATABASE_URL 環境變數。請檢查您的 .env 檔案。")
    sys.exit(1)

# --- 步驟 3: 建立資料庫連接與會話 ---
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    print("資料庫連接成功。")
except Exception as e:
    print(f"資料庫連接失敗: {e}")
    sys.exit(1)

# --- 步驟 4: 執行核心的 UPDATE 邏輯 ---
def reset_all_student_statuses():
    """
    將所有學生的 status 欄位，重置為 NOT_ARRIVED。
    為了最高效率，我們直接使用 SQLAlchemy Core 的 text() 來執行原生 SQL。
    """
    try:
        print("開始重置所有學生的狀態...")
        
        # 我們直接使用 UPDATE ... FROM ... WHERE 的語法，效率最高
        # 但一個簡單的 UPDATE 即可
        stmt = text(
            "UPDATE students SET status = :new_status"
        ).bindparams(
            new_status=StudentStatus.NOT_ARRIVED.name # 使用 .name 獲取英文鍵名
        )
        
        result = db.execute(stmt)
        db.commit()
        
        # result.rowcount 會告訴我們總共有多少行被更新了
        print(f"成功！總共有 {result.rowcount} 位學生的狀態被重置為 'NOT_ARRIVED'。")
        
    except Exception as e:
        print(f"執行狀態重置時出錯: {e}")
        db.rollback()
    finally:
        db.close()
        print("資料庫連接已關閉。")

# --- 步驟 5: 執行主函式 ---
if __name__ == "__main__":
    reset_all_student_statuses()