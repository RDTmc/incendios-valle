"""Debug endpoint to inspect uploaded file bytes before Lambda processing."""
from fastapi import FastAPI, UploadFile, File
from typing import Annotated
import uvicorn

DEBUG_APP = FastAPI()

@DEBUG_APP.post("/debug-upload")
def debug_upload(file: Annotated[UploadFile, File()]):
    contents = file.file.read()
    first_bytes = contents[:32].hex()
    size = len(contents)
    content_type = file.content_type
    filename = file.filename

    as_text = contents[:100].decode("utf-8", errors="replace")

    return {
        "size": size,
        "content_type": content_type,
        "filename": filename,
        "first_32_bytes_hex": first_bytes,
        "first_100_as_utf8": as_text,
        "valid_jpeg_header": first_bytes.startswith("ffd8"),
        "has_utf8_replacement": "efbfbd" in first_bytes,
    }

if __name__ == "__main__":
    uvicorn.run(DEBUG_APP, host="0.0.0.0", port=8001)
