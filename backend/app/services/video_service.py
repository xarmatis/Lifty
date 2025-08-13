import os
import uuid
from fastapi import UploadFile

# Folder inside the container to save uploads
UPLOAD_DIR = "/app/uploads"

# Make sure the directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def handle_upload(file: UploadFile) -> str:
    """
    Save the uploaded file to UPLOAD_DIR and return a unique video ID.
    """
    # Generate a unique filename to avoid collisions
    file_ext = os.path.splitext(file.filename)[1]
    video_id = str(uuid.uuid4())
    saved_filename = f"{video_id}{file_ext}"
    saved_path = os.path.join(UPLOAD_DIR, saved_filename)

    # Read the file contents and write to disk
    with open(saved_path, "wb") as f:
        content = await file.read()
        f.write(content)

    print(f"Saved video {file.filename} as {saved_filename}")
    return video_id
