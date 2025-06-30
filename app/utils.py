import json
from ultralytics import YOLO
import cv2
import numpy as np
import tempfile
import os
import base64


YOLO_MODEL_PATH = "/app/app/models/last.pt" # Hoặc đường dẫn tuyệt đối/đúng của bạn

def load_model(yolo_path: str):
    """Tải mô hình YOLO."""
    print(f"Loading YOLO model from: {yolo_path}")
    try:
        model = YOLO(yolo_path)
        print("YOLO model loaded successfully.")
        return model
    except Exception as e:
        print(f"Error loading YOLO model: {e}")
        raise

def process_frame(video_bytes: bytes, yolo_model):
    """
    Xử lý một video bằng cách chạy mô hình YOLO để theo dõi hoặc phát hiện đối tượng,
    tạo ra một video mới với các khung hình đã được chú thích.
    Video đã xử lý được trả về dưới dạng các chunk bytes để streaming.
    """
    print("\n--- process_frame: Starting video processing ---")
    
    # 1. Ghi dữ liệu video đầu vào vào một tệp tạm thời
    temp_input_video_file = None
    temp_output_video_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_in:
            tmp_in.write(video_bytes)
            temp_input_video_file = tmp_in.name
        print(f"process_frame: Original video saved to temp file: {temp_input_video_file}")

        cap = cv2.VideoCapture(temp_input_video_file)
        if not cap.isOpened():
            print(f"Error: Could not open video file at {temp_input_video_file}. Is the file valid and accessible?")
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"process_frame: Video properties - FPS: {fps}, Width: {w}, Height: {h}, Total Frames: {total_frames}")

        if w == 0 or h == 0 or fps == 0:
            print(f"Error: Invalid video dimensions or FPS detected. W:{w}, H:{h}, FPS:{fps}. Cannot process.")
            return

        # 2. Chuẩn bị VideoWriter cho video đầu ra
        # Sử dụng 'mp4v' (MPEG-4) codec, đây là codec được hỗ trợ rộng rãi trong các trình duyệt.
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_out:
            temp_output_video_file = tmp_out.name

        writer = cv2.VideoWriter(temp_output_video_file, fourcc, fps, (w, h))

        if not writer.isOpened():
            print(f"Error: Could not open video writer for {temp_output_video_file} with FOURCC {fourcc} at {fps} FPS and size ({w}, {h}). Check codec support.")
            return

        frame_count = 0
        frames_written = 0
        print("process_frame: Starting frame reading and processing loop...")
        while True:
            ret, frame = cap.read()
            if not ret:
                print(f"process_frame: Reached end of video or failed to read frame. Read {frame_count} frames.")
                break

            frame_count += 1
            
            # --- DỰ ĐOÁN / CHÚ THÍCH BẰNG YOLO ---
            # Lưu ý: yolo.track() thích hợp cho video vì nó duy trì ID đối tượng giữa các khung hình.
            # Nếu chỉ muốn phát hiện từng khung hình độc lập, dùng yolo(frame).
            results = yolo_model(frame) # Sử dụng yolo_model(frame) cho phát hiện đơn giản

            # Lấy khung hình đã chú thích
            # results[0].plot() trả về một mảng numpy (ảnh) của khung hình đã chú thích.
            annotated_frame = results[0].plot() 
            
            writer.write(annotated_frame)
            frames_written += 1
            
            # Print tiến độ để dễ debug với video dài
            if frame_count % 50 == 0:
                print(f"process_frame: Processed {frame_count}/{total_frames} frames.")

        cap.release()
        writer.release()
        print(f"process_frame: Video processing finished. Total frames written to output: {frames_written}")
        print(f"process_frame: Annotated video saved temporarily to: {temp_output_video_file}")

        # 3. Đọc tệp video đã xử lý và stream các chunk
        if frames_written == 0:
            print(f"WARNING: No frames were written to the output video '{temp_output_video_file}'. The output file might be empty or invalid.")
            # Có thể trả về một chunk rỗng hoặc raise lỗi ở đây nếu muốn dừng sớm

        with open(temp_output_video_file, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024) # Đọc 1MB mỗi lần
                if not chunk:
                    break
                yield chunk
        print("process_frame: Finished streaming video chunks.")

    except Exception as e:
        print(f"CRITICAL ERROR in process_frame: {e}")
        import traceback
        traceback.print_exc() # In stack trace để debug
    finally:
        # 4. Dọn dẹp các tệp tạm thời
        print("process_frame: Cleaning up temporary files...")
        if temp_input_video_file and os.path.exists(temp_input_video_file):
            os.remove(temp_input_video_file)
            print(f"process_frame: Deleted {temp_input_video_file}")
        
        # *** QUAN TRỌNG ĐỂ DEBUG: COMMENT DÒNG NÀY ĐỂ GIỮ LẠI FILE OUTPUT VÀ KIỂM TRA THỦ CÔNG ***
        # if temp_output_video_file and os.path.exists(temp_output_video_file):
        #     os.remove(temp_output_video_file)
        #     print(f"process_frame: Deleted {temp_output_video_file}")
        # ***********************************************************************************
        print("--- process_frame: Cleanup complete ---")

# Giữ nguyên hàm save_feedback nếu bạn cần nó
def save_feedback(data: dict, path: str):
    try:
        with open(path, 'r+', encoding='utf-8') as f:
            fb = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        fb = []
    fb.append(data)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(fb, f, ensure_ascii=False, indent=2)