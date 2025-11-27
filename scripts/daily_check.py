# 檔案路徑: scripts/daily_check.py (v1.0 - 單一全域時間版本)
# 職責: 在每日指定時間，檢查所有學生的狀態，找出異常情況並發出通知。

import os
import sys
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# --- 步驟 1: 將專案根目錄添加到 Python 路徑中 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(ROOT_DIR)

# 導入我們需要的模型
from app.models import Student, StudentStatus, User, UserRole, Class

# --- 步驟 2: 加載環境變數 ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
# 從 .env 讀取我們定義的全域檢查時間
DAILY_CHECK_TIME = os.getenv("DAILY_CHECK_TIME", "20:00") # 提供一個預設值

if not DATABASE_URL:
    print("錯誤：找不到 DATABASE_URL 環境變數。")
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

# --- 步驟 4: 執行核心的 SELECT 邏輯 ---
def perform_daily_check():
    """
    找出所有機構中，狀態不是 'NOT_ARRIVED' 或 'PICKUP_COMPLETED' 的學生，
    並將名單發送給所有相關教職員。
    """
    try:
        print(f"開始執行全域每日健康檢查 (設定時間: {DAILY_CHECK_TIME})...")
        
        # 定義哪些狀態是需要被報告的「異常」狀態
        abnormal_statuses = [
            StudentStatus.ARRIVED.name,
            StudentStatus.READY_FOR_PICKUP.name,
            StudentStatus.HOMEWORK_PENDING.name,
            StudentStatus.PARENT_EN_ROUTE.name,
        ]
        
        # 查詢所有狀態異常的學生，並帶出他們的班級名稱
        stmt = select(Student.full_name, Class.name.label("class_name")).join(
            Class, Student.class_id == Class.id
        ).where(
            Student.status.in_(abnormal_statuses)
        ).order_by(
            Class.name, Student.full_name
        )
        
        results = db.execute(stmt).all()
        
        if not results:
            print("檢查完成：所有學生的狀態均正常 (NOT_ARRIVED 或 PICKUP_COMPLETED)。無需發送通知。")
            return

        # --- 如果發現了異常學生，則準備並發送通知 ---
        print(f"發現 {len(results)} 位狀態異常的學生！準備發送通知...")
        
        # 構造通知內容
        report_lines = [f"【每日異常狀態報告 - {DAILY_CHECK_TIME}】", "以下學生在檢查時狀態異常，請老師關注："]
        for student_name, class_name in results:
            report_lines.append(f"- 班級: {class_name}, 學生: {student_name}")
        
        report_body = "\n".join(report_lines)
        
        # 找出系統中所有的老師、櫃檯和管理員
        staff_to_notify = db.query(User).filter(
            User.role.in_([UserRole.teacher.name, UserRole.receptionist.name, UserRole.admin.name]),
            User.status == 'active'
        ).all()
        
        if not staff_to_notify:
            print("警告：找到了異常學生，但系統中沒有任何活躍的教職員可以接收通知。")
            return
            
        # 模擬發送通知 (未來這裡會替換為真實的 Email 或 App 推播服務)
        staff_names = ", ".join([s.full_name for s in staff_to_notify])
        print("\n--- 模擬發送通知 ---")
        print(f"  收件人: {staff_names}")
        print(f"  標題: 每日異常狀態報告")
        print(f"  內容:\n{report_body}")
        print("----------------------\n")
        
        print("通知發送模擬完成。")

    except Exception as e:
        print(f"執行每日檢查時出錯: {e}")
    finally:
        db.close()
        print("資料庫連接已關閉。")

# --- 步驟 5: 執行主函式 ---
if __name__ == "__main__":
    perform_daily_check()
