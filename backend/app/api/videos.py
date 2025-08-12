from fastapi import APIRouter, UploadFile, File
from app.services import video_service

router = APIRouter()

@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    video_id = await video_service.handle_upload(file)
    return {"video_id": video_id, "status": "processing"}
