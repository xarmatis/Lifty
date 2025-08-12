import uuid
from pathlib import Path
import shutil

UPLOAD_DIR = Path("/tmp/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

async def handle_upload(file):
    video_id = str(uuid.uuid4())
    out_path = UPLOAD_DIR / f"{video_id}.mp4"
    with out_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # TODO: enqueue Celery job for processing
    return video_id
