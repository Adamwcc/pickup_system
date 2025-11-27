# 檔案路徑: app/core/config.py

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# vvv --- 【核心修改：使用 pathlib 來計算路徑】 --- vvv
# Path(__file__) -> 獲取當前檔案的路徑物件 (C:/.../app/core/config.py)
# .resolve()    -> 解析為絕對路徑，消除任何符號連結
# .parent        -> 獲取父目錄 (C:/.../app/core)
# .parent        -> 再次獲取父目錄 (C:/.../app)
# .parent        -> 第三次獲取父目錄 (C:/.../pickup_system) -> 這就是我們的專案根目錄！
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = ROOT_DIR / ".env"  # 使用 / 運算符來拼接路徑，比 os.path.join 更優雅
# ^^^ --- 【核心修改：使用 pathlib 來計算路徑】 --- ^^^

# 檢查 .env 檔案是否存在
if not ENV_PATH.exists():
    print(f"警告：在預期路徑 {ENV_PATH} 中找不到 .env 檔案。")
    print("系統將無法獲取必要的設定，預計將會啟動失敗。")

# 載入 .env 檔案
load_dotenv(dotenv_path=ENV_PATH)

class Settings(BaseSettings):
    """
    應用程式的設定類，使用 Pydantic 進行類型驗證。
    它會自動從環境變數或 .env 檔案中讀取設定。
    """
    # --- 資料庫設定 ---
    # 為 DATABASE_URL 提供一個預設值。
    # 如果 .env 中定義了 DATABASE_URL，Pydantic 會使用 .env 中的值。
    # 如果 .env 中沒有定義，Pydantic 會使用下面這個預設的 SQLite 路徑。
    DATABASE_URL: str

    # --- JWT 認證設定 ---
    # 這是我們未來用於簽發 JWT 的秘密金鑰
    JWT_SECRET_KEY: str
    # 簽名演算法
    JWT_ALGORITHM: str = "HS256"
    # Token 的有效期限（分鐘）
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # vvv --- 【請追加這一行】 --- vvv
    # 每日健康檢查的時間
    DAILY_CHECK_TIME: str = "20:00"
    # ^^^ --- 【請追加這一行】 --- ^^^

    # --- 專案資訊 ---
    PROJECT_NAME: str = "Pickup System"
    API_V1_STR: str = "/api/v1"

    # --- Cron Job 秘密令牌 (來自我們之前的設計) ---
    CRON_SECRET: str | None = None # 設為可選，如果 .env 沒定義也不會報錯

    class Config:
        # Pydantic v2 的設定方式
        case_sensitive = True
        # 指定 .env 檔案的編碼
        env_file_encoding = 'utf-8'

# 創建一個全域可用的 Settings 實例
# 我們的應用程式將從這裡導入所有設定
settings = Settings()
