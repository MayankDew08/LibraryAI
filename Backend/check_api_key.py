import os
from dotenv import load_dotenv

load_dotenv()

print(f"Environment GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY')}")
print(f"Direct value: REDACTED_GOOGLE_API_KEY")

# Now import settings
from app.config.settings import GEMINI_API_KEY
print(f"Settings GEMINI_API_KEY: {GEMINI_API_KEY}")
print(f"Length: {len(GEMINI_API_KEY)}")
