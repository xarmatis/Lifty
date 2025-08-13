
from fastapi import APIRouter, UploadFile, File
from app.services.video_service import handle_upload  # import from services

router = APIRouter()

@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    video_id = await handle_upload(file)
    return {"video_id": video_id, "status": "processing"}
