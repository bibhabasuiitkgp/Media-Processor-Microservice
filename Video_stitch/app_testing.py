from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import shutil
import os
from datetime import datetime
import uuid
from Video import VideoStitcher
import logging

app = FastAPI(title="Mansio Video Stitching API")

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

# Create directories
UPLOAD_DIR = "static/uploads/videos"
OUTPUT_DIR = "static/processed/videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize VideoStitcher
stitcher = VideoStitcher(user_login="bibhabasuiitkgp")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("video_stitching.log"),
    ],
)
logger = logging.getLogger(__name__)

@app.post("/stitch/videos/")
async def stitch_videos(files: List[UploadFile] = File(...)):
    """
    Upload multiple videos and stitch them together with Mansio watermark
    Returns the URL of the stitched video
    """
    try:
        # Validate files
        for file in files:
            if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid video format for file: {file.filename}"
                )

        # Create temporary directory for uploaded files
        temp_dir = os.path.join(UPLOAD_DIR, str(uuid.uuid4()))
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # Save uploaded files
            video_paths = []
            for file in files:
                temp_path = os.path.join(temp_dir, file.filename)
                with open(temp_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                video_paths.append(temp_path)

            # Sort videos by filename
            video_paths.sort()

            # Generate output filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            output_filename = f"mansio_stitched_{timestamp}_{unique_id}.mp4"
            output_path = os.path.join(OUTPUT_DIR, output_filename)

            # Stitch videos
            success, message = stitcher.process_videos(  # Changed from stitch_videos to process_videos
                video_paths,
                output_path
            )

            if success:
                return {
                    "status": "success",
                    "message": message,
                    "stitched_video_url": f"/static/processed/videos/{output_filename}"
                }
            else:
                raise HTTPException(status_code=500, detail=message)

        finally:
            # Clean up temporary files
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    except Exception as e:
        logger.error(f"Error in video stitching: {str(e)}")
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)