from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from Image import ImageProcessor
import uuid

app = FastAPI(title="Image Enhancement API")

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

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize ImageProcessor
processor = ImageProcessor()


@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse("static/index.html")


@app.post("/enhance/")
async def enhance_image(file: UploadFile = File(...)):
    try:
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{str(uuid.uuid4())}{file_extension}"
        input_path = os.path.join(UPLOAD_DIR, f"input_{unique_filename}")
        output_path = os.path.join(UPLOAD_DIR, f"output_{unique_filename}")

        # Save uploaded file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process image
        success, message = processor.adjust_brightness(input_path, output_path)

        if not success:
            raise HTTPException(status_code=400, detail=message)

        print(f"Image enhanced successfully: {output_path}")
        # Return full URLs for both original and enhanced images
        return {
            "original": f"/static/uploads/input_{unique_filename}",
            "enhanced": f"/static/uploads/output_{unique_filename}",
            "message": "Image enhanced successfully",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
