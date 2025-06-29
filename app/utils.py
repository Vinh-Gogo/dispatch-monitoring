# app\utils.py
import json
from ultralytics import YOLO
from io import BytesIO
import cv2
import numpy as np
import tempfile
import os
import base64

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

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        # Run YOLO tracking on the frame, persisting tracks between frames
        results = yolo.track(frame, persist=True)
        
        # Check if any objects were detected/tracked
        if results and results[0].boxes:
            print(f"Frame {frame_count}: Detected {len(results[0].boxes)} objects.")
            # Visualize the results on the frame
            annotated = results[0].plot()
            writer.write(annotated)
        else:
            print(f"Frame {frame_count}: No objects detected.")
            # If no objects are detected, write the original frame to maintain video flow
            writer.write(frame)


    cap.release()
    writer.release()

    # Đọc file đã annotate và yield từng chunk
    with open(out_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            yield chunk

    os.remove(video_path)
    os.remove(out_path)

def get_detection_frames_data(video_bytes: bytes, yolo):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video_bytes)
        video_path = tmp.name

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Calculate interval to get roughly 2 frames per second (0.5s interval)
    # Ensure interval is at least 1 frame
    sample_interval_frames = max(1, round(fps / 2)) 

    all_detected_frames_data = []
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        
        # Process frame only at specified intervals
        if frame_count % sample_interval_frames == 0:
            results = yolo(frame)
            
            if results and results[0].boxes:
                annotated_frame = results[0].plot()
                _, buffer = cv2.imencode('.jpg', annotated_frame)
                encoded_image = base64.b64encode(buffer).decode('utf-8')

                detections_info = []
                for box in results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    class_id = int(box.cls[0].item())
                    confidence = round(float(box.conf[0].item()), 2)
                    class_name = yolo.names[class_id]
                    
                    detection = {
                        "class": class_name,
                        "confidence": confidence,
                        "box_coordinates": [x1, y1, x2, y2]
                    }
                    if hasattr(box, 'id') and box.id is not None:
                        track_id = int(box.id[0].item())
                        detection["track_id"] = track_id
                    
                    detections_info.append(detection)
                
                all_detected_frames_data.append({
                    "image": encoded_image,
                    "detections": detections_info,
                    "frame_number": frame_count
                })

    cap.release()
    os.remove(video_path)
    
    return all_detected_frames_data

def save_feedback(data: dict, path: str):
    try:
        with open(path, 'r+', encoding='utf-8') as f:
            fb = json.load(f)
    except:
        fb = []
    fb.append(data)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(fb, f, ensure_ascii=False, indent=2)