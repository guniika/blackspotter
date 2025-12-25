import cv2
import time
import sqlite3
import os
from pathlib import Path
from ultralytics import YOLO

# 1. SETUP PATHS
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "best.pt"
DB_PATH = BASE_DIR / "blackspotter_logs.db"
VIDEO_PATH = BASE_DIR / "crash_test.mp4"

# 2. LOAD AI MODELS
model = YOLO('yolov8n.pt') 
if not MODEL_PATH.exists():
    print(f"ERROR: 'best.pt' NOT FOUND in {BASE_DIR}")
    exit()
specialist = YOLO(str(MODEL_PATH)) 

# 3. DATABASE LOGGER
def log_to_db(tier):
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS incidents 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      timestamp TEXT, tier TEXT)''')
        conn.execute("INSERT INTO incidents (timestamp, tier) VALUES (?, ?)", 
                     (time.strftime('%Y-%m-%d %H:%M:%S'), tier))
        conn.commit()

# 4. MAIN LOOP
cap = cv2.VideoCapture(str(VIDEO_PATH)) 
car_history = {}
alert_memory = {"active": False, "start": 0}

print("BlackSpotter AI: Active and Monitoring...")

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    results = model.track(frame, persist=True, classes=[2, 7], verbose=False)
    crash_results = specialist(frame, conf=0.3, verbose=False)
    current_tier = "SAFE"

    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        ids = results[0].boxes.id.cpu().numpy()
        for i, obj_id in enumerate(ids):
            center = ((boxes[i][0] + boxes[i][2])/2, (boxes[i][1] + boxes[i][3])/2)
            if obj_id in car_history:
                speed = ((center[0]-car_history[obj_id][0])**2 + (center[1]-car_history[obj_id][1])**2)**0.5
                if speed < 1 and len(crash_results[0].boxes) > 0:
                    current_tier = "TIER 3: CRITICAL IMPACT"
            car_history[obj_id] = center

    if current_tier == "TIER 3: CRITICAL IMPACT" and not alert_memory["active"]:
        log_to_db(current_tier)
        alert_memory = {"active": True, "start": time.time()}

    if alert_memory["active"] and (time.time() - alert_memory["start"] > 15):
        alert_memory["active"] = False

    cv2.imshow("BlackSpotter AI Dashboard", results[0].plot())
    if cv2.waitKey(1) & 0xFF == ord("q"): break

cap.release()
cv2.destroyAllWindows()