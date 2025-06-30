from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import the utility functions
from app.utils import load_model, process_frame, YOLO_MODEL_PATH # Ensure YOLO_MODEL_PATH is imported

app = FastAPI(title="Dispatch Monitoring System")

# Serve static files (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")
# Configure Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Load YOLO model once when the application starts
try:
    yolo_model = load_model(yolo_path=YOLO_MODEL_PATH)
except Exception as e:
    print(f"Application startup error: {e}. Exiting.")
    # You might want to handle this more gracefully in production
    # For now, it's good to let it fail if the model can't load.
    yolo_model = None # Set to None to prevent further errors if not loaded

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process_video/")
async def process_video_for_display(file: UploadFile = File(...)):
    if yolo_model is None:
        return JSONResponse(content={"message": "AI model not loaded. Cannot process video."}, status_code=500)

    print(f"main.py: Received file '{file.filename}' for processing.")
    
    try:
        input_video_bytes = await file.read()
        
        # Calling process_frame which returns a generator of video chunks
        video_stream_generator = process_frame(input_video_bytes, yolo_model)
        
        # Return StreamingResponse with the generator and correct media type
        # It's crucial that "video/mp4" is correct and the video file itself is valid.
        return StreamingResponse(video_stream_generator, media_type="video/mp4")
    except Exception as e:
        print(f"main.py: Error during video processing endpoint: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(content={"message": f"Server error during video processing: {e}"}, status_code=500)
