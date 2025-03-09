from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from datetime import datetime
import uuid
from Video import VideoProcessor
import logging

app = FastAPI(title="Video Enhancement API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create directories if they don't exist
UPLOAD_DIR = "static/uploads/videos"
OUTPUT_DIR = "static/processed/videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize VideoProcessor with specified timestamp and user login
processor = VideoProcessor(
    user_login="bibhabasuiitkgp",
    timestamp="2025-03-09 05:51:56"  # Current UTC timestamp
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("video_processing.log"),
    ],
)
logger = logging.getLogger(__name__)

@app.post("/enhance/video/")
async def enhance_video(file: UploadFile = File(...)):
    """
    Upload and enhance a video file with Mansio watermark
    Returns the URL of the enhanced video
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            raise HTTPException(status_code=400, detail="Invalid video format")

        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{str(uuid.uuid4())}{file_extension}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        input_path = os.path.join(UPLOAD_DIR, f"input_{unique_filename}")
        output_path = os.path.join(OUTPUT_DIR, f"enhanced_{timestamp}_{unique_filename}")
        
        # Save uploaded file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process video with Mansio watermark
        success, message = processor.process_video(input_path, output_path)
        
        # Clean up input file
        if os.path.exists(input_path):
            os.remove(input_path)
        
        if success:
            return {
                "status": "success",
                "message": message,
                "enhanced_video_url": f"/static/processed/videos/enhanced_{timestamp}_{unique_filename}",
                "watermark_info": {
                    "user": "bibhabasuiitkgp",
                    "timestamp": "2025-03-09 05:51:56",
                    "brand": "Mansio"
                }
            }
        else:
            raise HTTPException(status_code=500, detail=message)
            
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        # Clean up any leftover files
        if 'input_path' in locals() and os.path.exists(input_path):
            os.remove(input_path)
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)