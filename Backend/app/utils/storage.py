import os
from datetime import datetime, timezone

BASE_DIR = "static"

def save_file(file, folder: str):
    """Save uploaded file to static folder and return file path"""
    filename = f"{datetime.now(timezone.utc).timestamp()}_{file.filename}"
    path = os.path.join(BASE_DIR, folder)
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path
