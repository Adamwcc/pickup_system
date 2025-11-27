# 檔案路徑: app/core/logging_config.py

import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

# --- 1. 定義日誌檔案的路徑 ---
# 我們將日誌檔案存放在專案的根目錄下的一個名為 'logs' 的資料夾中
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = ROOT_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True) # 確保 logs 資料夾存在
LOG_FILE = LOGS_DIR / "app.log"

# --- 2. 定義日誌格式 ---
# 一個好的日誌格式，應該包含時間、日誌級別、模組名稱、以及日誌訊息
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

# --- 3. 創建並配置根日誌記錄器 (Root Logger) ---
# 我們直接配置根記錄器，這樣我們專案中所有模組的日誌都會繼承這個配置
logger = logging.getLogger()
logger.setLevel(logging.INFO) # 設定日誌記錄的最低級別為 INFO

# --- 4. 創建處理器 (Handlers) ---
# 處理器決定了日誌要被發送到哪裡

# 處理器 A: 輸出到控制台 (StreamHandler)
# 這讓我們在開發和運行時，能即時看到日誌
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(stream_handler)

# 處理器 B: 輸出到檔案 (TimedRotatingFileHandler)
# 這會將日誌寫入到 app.log 檔案中
# TimedRotatingFileHandler 會自動按時間（例如每天）分割日誌檔案，防止單一檔案過大
# when='D' 表示每天分割一次, backupCount=7 表示最多保留 7 個舊的日誌檔案
file_handler = TimedRotatingFileHandler(
    LOG_FILE, 
    when='D', 
    interval=1, 
    backupCount=7, 
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(file_handler)

# --- 5. 提供一個簡單的函數，供其他模組調用以獲取配置好的 logger ---
def get_logger(name: str) -> logging.Logger:
    """
    獲取一個以指定名稱命名的 logger 實例。
    由於我們已經配置了根 logger，所以這裡獲取到的任何 logger 都會自動繼承那些配置。
    """
    return logging.getLogger(name)

