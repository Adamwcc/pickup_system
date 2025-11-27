# 檔案路徑: scripts/daily_check.py (v2.0 - 黃金標準版)

import os
import sys
import logging
import time
from sqlalchemy import select

# --- 導入 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(ROOT_DIR)

from app.core.config import settings
from app.database import SessionLocal
from app.core.logging_config import get_logger
from app.models import Student, StudentStatus, User, UserRole, Class

# --- 全域變數 ---
logger = get_logger(__name__)

# --- 主邏輯函數 ---
def main():
    db = None # db 作為 main 函數的局部變數
    try:
        # --- 步驟 1: 建立資料庫連接 ---
        db = SessionLocal()
        logger.info("資料庫會話創建成功。")

        # --- 步驟 2: 執行核心 SELECT 邏輯 ---
        logger.info(f"開始執行全域每日健康檢查 (設定時間: {settings.DAILY_CHECK_TIME})...")
        
        abnormal_statuses = [
            StudentStatus.ARRIVED.name,
            StudentStatus.READY_FOR_PICKUP.name,
            StudentStatus.HOMEWORK_PENDING.name,
            StudentStatus.PARENT_EN_ROUTE.name,
        ]
        
        stmt = select(Student.full_name, Class.name.label("class_name")).join(
            Class, Student.class_id == Class.id
        ).where(
            Student.status.in_(abnormal_statuses)
        ).order_by(
            Class.name, Student.full_name
        )
        
        results = db.execute(stmt).all()
        
        if not results:
            logger.info("檢查完成：所有學生的狀態均正常。無需發送通知。")
            # 正常結束，直接跳到 finally 塊進行清理
            return

        logger.info(f"發現 {len(results)} 位狀態異常的學生！準備發送通知...")
        
        report_lines = [f"【每日異常狀態報告 - {settings.DAILY_CHECK_TIME}】", "以下學生在檢查時狀態異常，請老師關注："]
        for student_name, class_name in results:
            report_lines.append(f"- 班級: {class_name}, 學生: {student_name}")
        
        report_body = "\n".join(report_lines)
        
        staff_to_notify = db.query(User).filter(
            User.role.in_([UserRole.teacher.name, UserRole.receptionist.name, UserRole.admin.name]),
            User.status == 'active'
        ).all()
        
        if not staff_to_notify:
            logger.warning("找到了異常學生，但系統中沒有任何活躍的教職員可以接收通知。")
            return
            
        staff_names = ", ".join([s.full_name for s in staff_to_notify])
        
        notification_log_message = (
            f"\n--- 模擬發送通知 ---\n"
            f"  收件人: {staff_names}\n"
            f"  標題: 每日異常狀態報告\n"
            f"  內容:\n{report_body}\n"
            f"----------------------"
        )
        logger.info(notification_log_message)
        
        logger.info("通知發送模擬完成。")

    except Exception as e:
        logger.error(f"腳本執行過程中發生致命錯誤: {e}", exc_info=True)
        if db:
            db.rollback() # 對於 SELECT 為主的腳本，rollback 不是必須的，但保留是個好習慣
        sys.exit(1)

    finally:
        # --- 統一的清理 ---
        if db and db.is_active:
            db.close()
            logger.info("資料庫連接已關閉。")
        
        # --- 終極日誌沖刷 ---
        logging.shutdown()
        time.sleep(0.1)

# --- 腳本入口 ---
if __name__ == "__main__":
    main()
