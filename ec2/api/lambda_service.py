import os
import uuid
from pathlib import Path

UPLOAD_DIR = Path("/app/data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = os.environ.get("UPLOAD_BASE_URL", "https://api.keogh.lat/uploads")

def upload_image(file_bytes: bytes, content_type: str) -> str:
    ext = "jpg" if content_type == "image/jpeg" else "png"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = UPLOAD_DIR / filename
    with open(filepath, "wb") as f:
        f.write(file_bytes)
    return f"{BASE_URL}/{filename}"
