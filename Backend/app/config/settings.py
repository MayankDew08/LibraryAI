"""
Application settings and environment variables
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Gemini AI Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Hugging Face Configuration
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")

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

# JWT Authentication Settings
SECRET_KEY = os.getenv("secret_key", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("algorithm", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("access_token_expire_minutes", "1440"))
