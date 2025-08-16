from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services import video_service

router = APIRouter()

@router.post("/analyze-video/")
async def analyze_video(file: UploadFile = File(...)):
    if not file:
        print("No file received!")
    else:
        print("Received file:", file.filename)
        
    if not file.filename.lower().endswith((".mp4", ".mov", ".avi")):
       raise HTTPException(status_code=400, detail="Invalid video format")

    result = await video_service.process_video(file)
    return result
