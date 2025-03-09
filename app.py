from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import shutil
import os
from datetime import datetime
import uuid
import logging
from Image.Image import ImageProcessor
from video_enhancement.Video import VideoProcessor
from Video_stitch.Video import VideoStitcher

app = FastAPI(title="Mansio Media Processing API")

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

# Create necessary directories
DIRS = {
    "image": {
        "upload": "static/uploads/images",
        "processed": "static/processed/images"
    },
    "video": {
        "upload": "static/uploads/videos",
        "processed": "static/processed/videos"
    }
}

for media_type in DIRS.values():
    for dir_path in media_type.values():
        os.makedirs(dir_path, exist_ok=True)

# Initialize processors with current timestamp and user
CURRENT_USER = "bibhabasuiitkgp"
CURRENT_TIMESTAMP = "2025-03-09 05:59:54"

image_processor = ImageProcessor()
video_processor = VideoProcessor(user_login=CURRENT_USER, timestamp=CURRENT_TIMESTAMP)
video_stitcher = VideoStitcher(user_login=CURRENT_USER)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("media_processing.log"),
    ],
)
logger = logging.getLogger(__name__)

@app.post("/enhance/image/")
async def enhance_image(file: UploadFile = File(...)):
    """
    Upload and enhance a single image
    Returns the URL of the enhanced image
    """
    try:
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
            raise HTTPException(status_code=400, detail="Invalid image format")

        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{str(uuid.uuid4())}{file_extension}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        input_path = os.path.join(DIRS["image"]["upload"], f"input_{unique_filename}")
        output_path = os.path.join(DIRS["image"]["processed"], f"enhanced_{timestamp}_{unique_filename}")
        
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        success, message = image_processor.adjust_brightness(input_path, output_path)
        
        if os.path.exists(input_path):
            os.remove(input_path)
        
        if success:
            return {
                "status": "success",
                "message": message,
                "enhanced_image_url": f"/static/processed/images/enhanced_{timestamp}_{unique_filename}"
            }
        else:
            raise HTTPException(status_code=500, detail=message)
            
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        if 'input_path' in locals() and os.path.exists(input_path):
            os.remove(input_path)
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/enhance/video/")
async def enhance_video(file: UploadFile = File(...)):
    """
    Upload and enhance a video with Mansio watermark
    Returns the URL of the enhanced video
    """
    try:
        if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            raise HTTPException(status_code=400, detail="Invalid video format")

        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{str(uuid.uuid4())}{file_extension}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        input_path = os.path.join(DIRS["video"]["upload"], f"input_{unique_filename}")
        output_path = os.path.join(DIRS["video"]["processed"], f"enhanced_{timestamp}_{unique_filename}")
        
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        success, message = video_processor.process_video(input_path, output_path)
        
        if os.path.exists(input_path):
            os.remove(input_path)
        
        if success:
            return {
                "status": "success",
                "message": message,
                "enhanced_video_url": f"/static/processed/videos/enhanced_{timestamp}_{unique_filename}",
                "watermark_info": {
                    "user": CURRENT_USER,
                    "timestamp": CURRENT_TIMESTAMP,
                    "brand": "Mansio"
                }
            }
        else:
            raise HTTPException(status_code=500, detail=message)
            
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        if 'input_path' in locals() and os.path.exists(input_path):
            os.remove(input_path)
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
        raise HTTPException(status_code=500, detail=str(e))

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
        temp_dir = os.path.join(DIRS["video"]["upload"], str(uuid.uuid4()))
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
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            output_filename = f"mansio_stitched_{timestamp}_{unique_id}.mp4"
            output_path = os.path.join(DIRS["video"]["processed"], output_filename)

            # Stitch videos
            success, message = video_stitcher.process_videos(
                video_paths,
                output_path
            )

            if success:
                return {
                    "status": "success",
                    "message": message,
                    "stitched_video_url": f"/static/processed/videos/{output_filename}",
                    "watermark_info": {
                        "user": CURRENT_USER,
                        "timestamp": CURRENT_TIMESTAMP,
                        "brand": "Mansio"
                    }
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