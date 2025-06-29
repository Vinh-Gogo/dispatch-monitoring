# app\utils.py
import json
from ultralytics import YOLO
from io import BytesIO
import cv2
import numpy as np
import tempfile
import os

def load_model(yolo_path: str):
    return YOLO(yolo_path)

def process_frame(video_bytes: bytes, yolo):
    # Lưu video bytes vào file tạm
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video_bytes)
        video_path = tmp.name

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Ghi video output vào bộ nhớ
    output = BytesIO()
    out_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = yolo(frame)
        labels = results[0].names
        boxes = results[0].boxes
        class_ids = results[0].boxes.cls.cpu().numpy().astype(int)

        found_khay = any(labels[i] == "khay" for i in class_ids)
        found_doan = any(labels[i] == "đồ ăn" for i in class_ids)

        if found_khay and found_doan:
            annotated = results[0].plot()
            writer.write(annotated)

    cap.release()
    writer.release()

    # Đọc file đã annotate và yield từng chunk
    with open(out_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            yield chunk

    os.remove(video_path)
    os.remove(out_path)

def save_feedback(data: dict, path: str):
    try:
        with open(path, 'r+', encoding='utf-8') as f:
            fb = json.load(f)
    except:
        fb = []
    fb.append(data)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(fb, f, ensure_ascii=False, indent=2)
