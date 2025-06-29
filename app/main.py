from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.utils import load_model, process_frame, save_feedback, get_detection_frames_data

app = FastAPI(title="Dispatch Monitoring System")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

yolo_model = load_model(yolo_path="app/models/best.pt")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/predict/")
async def predict_video(file: UploadFile = File(...)):
    input_bytes = await file.read()
    video_stream = process_frame(input_bytes, yolo_model)
    return StreamingResponse(video_stream, media_type="video/mp4")

@app.post("/get_detection_data/")
async def get_detection_data(file: UploadFile = File(...)):
    input_bytes = await file.read()
    all_frames_data = get_detection_frames_data(input_bytes, yolo_model)
    return JSONResponse(content=all_frames_data)
