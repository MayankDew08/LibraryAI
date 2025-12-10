"""
Application settings and environment variables
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Gemini AI Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "REDACTED_GOOGLE_API_KEY")

# File Upload Settings
UPLOAD_DIR = "static"
ALLOWED_PDF_EXTENSIONS = {".pdf"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Audio Generation Settings
AUDIO_OUTPUT_DIR = os.path.join(UPLOAD_DIR, "podcasts")
AUDIO_FORMAT = "mp3"

# Database
DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL", "mysql+mysqldb://root:password@localhost:3306/library_db")
