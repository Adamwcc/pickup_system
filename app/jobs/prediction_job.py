import sys
import os
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# --- 設定 Python 環境，讓腳本能找到 app 模組 ---
# 將專案根目錄（pickup_system）添加到 Python 的搜尋路徑中
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)
# ---------------------------------------------

from app.database import SessionLocal, engine
from app.models import PickupNotification, PickupPrediction, Student
from sqlalchemy import func

def analyze_and_predict():
    """
    分析歷史接送數據並產生今日的預測。
    """
    db: Session = SessionLocal()
    print("--- 開始執行智慧預測任務 ---")

    try:
        # --- 1. 定義分析的時間範圍 ---
        today = datetime.utcnow().date()
        # 我們分析過去 14 天的數據
        analysis_start_date = today - timedelta(days=14)
        
        # --- 2. 定義「高峰時段」---
        # 假設下午 4 點到 6 點是接送高峰
        PEAK_HOUR_START = 16
        PEAK_HOUR_END = 18

        # --- 3. 查詢歷史數據 ---
        # 找出在過去 14 天的高峰時段內，每個學生的接送次數
        print(f"分析時間範圍: {analysis_start_date} 至 {today}")
        
        pickup_counts = db.query(
            PickupNotification.student_id,
            func.count(PickupNotification.id).label("pickup_count")
        ).filter(
            PickupNotification.created_at >= analysis_start_date,
            func.extract('hour', PickupNotification.created_at) >= PEAK_HOUR_START,
            func.extract('hour', PickupNotification.created_at) < PEAK_HOUR_END
        ).group_by(
            PickupNotification.student_id
        ).all()

        print(f"找到 {len(pickup_counts)} 位學生的歷史接送紀錄。")

        # --- 4. 找出「常客」---
        # 我們的定義：在過去 14 天的高峰時段內，接送次數超過 5 次的學生
        REGULAR_CUSTOMER_THRESHOLD = 5
        
        # 清除今天已有的舊預測，防止重複
        db.query(PickupPrediction).filter(func.date(PickupPrediction.prediction_date) == today).delete()

        prediction_count = 0
        for student_id, count in pickup_counts:
            if count >= REGULAR_CUSTOMER_THRESHOLD:
                # 這是一位常客，為他建立一條今天的預測紀錄
                print(f"找到常客: 學生ID={student_id}, 接送次數={count}。正在寫入預測...")
                
                new_prediction = PickupPrediction(
                    prediction_date=datetime.utcnow(),
                    student_id=student_id
                )
                db.add(new_prediction)
                prediction_count += 1
        
        # --- 5. 提交結果 ---
        db.commit()
        print(f"--- 任務完成！共為 {prediction_count} 位常客產生了預測。 ---")

    finally:
        db.close()

if __name__ == "__main__":
    analyze_and_predict()
