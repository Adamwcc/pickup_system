# 檔案路徑: scripts/daily_reset.py (v4.0 - 黃金標準版)

import os
import sys
import logging
import time
from sqlalchemy import text

# --- 導入 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(ROOT_DIR)

from app.database import SessionLocal
from app.core.logging_config import get_logger
from app.models import StudentStatus

# --- 全域變數 ---
logger = get_logger(__name__)

# --- 主邏輯函數 ---
def main():
    db = None # db 作為 main 函數的局部變數
    try:
        # --- 步驟 1: 建立資料庫連接 ---
        db = SessionLocal()
        logger.info("資料庫會話創建成功。")

        # --- 步驟 2: 執行核心 UPDATE 邏輯 ---
        logger.info("開始重置所有學生的狀態...")
        
        stmt = text(
            "UPDATE students SET status = :new_status"
        ).bindparams(
            new_status=StudentStatus.NOT_ARRIVED.name
        )
        
        result = db.execute(stmt)
        db.commit()
        
        logger.info(f"成功！總共有 {result.rowcount} 位學生的狀態被重置為 'NOT_ARRIVED'。")

    except Exception as e:
        logger.error(f"腳本執行過程中發生致命錯誤: {e}", exc_info=True)
        if db:
            db.rollback()
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
