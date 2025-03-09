# Media Processing API

A FastAPI-based API service for image and video processing, including enhancement and video stitching capabilities.

## Features

- Image Enhancement
  - Supports multiple image formats (PNG, JPG, JPEG, TIFF, BMP)
  - Automatic brightness adjustment
  - Processed images are stored with unique identifiers

- Video Enhancement
  - Supports multiple video formats (MP4, AVI, MOV, MKV)
  - Adds Mansio watermark
  - Includes user and timestamp information
  - Processed videos are stored with unique identifiers

- Video Stitching
  - Combine multiple videos into a single video
  - Maintains chronological order based on filenames
  - Adds Mansio watermark with metadata

## Tech Stack

- Python 3.x
- FastAPI
- uvicorn (ASGI server)
- Custom image and video processing modules:
  - `Image_Enhancement.Image`
  - `Video_enhancement.Video`
  - `Video_stitch.Video`

## Project Structure

```
.
├── static/
│   ├── uploads/
│   │   ├── images/
│   │   └── videos/
│   └── processed/
│       ├── images/
│       └── videos/
├── app.py
├── requirements.txt
└── media_processing.log
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mansio-media-processing
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

The application automatically creates the following directory structure for media storage:
- `/static/uploads/images`: Temporary storage for uploaded images
- `/static/uploads/videos`: Temporary storage for uploaded videos
- `/static/processed/images`: Storage for processed images
- `/static/processed/videos`: Storage for processed videos

## API Endpoints

### 1. Enhance Image
- **URL**: `/enhance/image/`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file`: Image file (PNG, JPG, JPEG, TIFF, BMP)
- **Response**:
```json
{
    "status": "success",
    "message": "Image enhanced successfully",
    "enhanced_image_url": "/static/processed/images/enhanced_[timestamp]_[uuid].extension"
}
```

### 2. Enhance Video
- **URL**: `/enhance/video/`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file`: Video file (MP4, AVI, MOV, MKV)
- **Response**:
```json
{
    "status": "success",
    "message": "Video enhanced successfully",
    "enhanced_video_url": "/static/processed/videos/enhanced_[timestamp]_[uuid].extension",
    "watermark_info": {
        "user": "username",
        "timestamp": "YYYY-MM-DD HH:MM:SS",
        "brand": "Mansio"
    }
}
```

### 3. Stitch Videos
- **URL**: `/stitch/videos/`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `files`: Multiple video files (MP4, AVI, MOV, MKV)
- **Response**:
```json
{
    "status": "success",
    "message": "Videos stitched successfully",
    "stitched_video_url": "/static/processed/videos/mansio_stitched_[timestamp]_[uuid].mp4",
    "watermark_info": {
        "user": "username",
        "timestamp": "YYYY-MM-DD HH:MM:SS",
        "brand": "Mansio"
    }
}
```

## Running the Application

1. Start the server:
```bash
python app.py
```
Or using uvicorn directly:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

2. Access the API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Error Handling

The API includes comprehensive error handling:
- Invalid file formats return 400 Bad Request
- Processing errors return 500 Internal Server Error
- All errors are logged to `media_processing.log`
- Automatic cleanup of temporary files in case of failures

## CORS Configuration

The API supports Cross-Origin Resource Sharing (CORS) with the following configuration:
- All origins allowed (`*`)
- All methods allowed
- All headers allowed
- Credentials supported

## Logging

- All operations are logged using Python's built-in logging
- Log format: `timestamp - level - message`
- Logs are written to both console and `media_processing.log` file

## Security Considerations

1. File validation for supported formats
2. Unique filename generation using UUID
3. Automatic cleanup of temporary files
4. Input/output path validation
