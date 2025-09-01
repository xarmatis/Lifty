from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from app.services import video_service

router = APIRouter()

@router.post("/analyze-video/")
async def analyze_video(
    file: UploadFile = File(...),
    exercise_type: str = Form("squat")
):
    if not file:
        print("No file received!")
    else:
        print("Received file:", file.filename)
        print("Exercise type:", exercise_type)
        
    # Debug file information
    print(f"File received: {file.filename}")
    print(f"File content type: {file.content_type}")
    
    # More robust file extension checking
    valid_extensions = (".mp4", ".mov", ".avi", ".MP4", ".MOV", ".AVI")
    if not file.filename.endswith(valid_extensions):
        print(f"Invalid file extension: {file.filename}")
        raise HTTPException(status_code=400, detail=f"Invalid video format. Supported formats: MP4, MOV, AVI (case insensitive)")
    
    print(f"File validation passed for: {file.filename}")

    result = await video_service.process_video(file, exercise_type)
    return result
