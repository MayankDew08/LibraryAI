"""Test Gemini API connection"""
import sys

# Test 1: Check API key is loaded
from app.config.settings import GEMINI_API_KEY
print(f"API Key loaded: {GEMINI_API_KEY[:20]}...{GEMINI_API_KEY[-10:]}")
print(f"API Key length: {len(GEMINI_API_KEY)}")

# Test 2: Try importing google-genai
try:
    from google import genai
    print(f"✓ google-genai imported successfully")
    print(f"  Version: {genai.__version__ if hasattr(genai, '__version__') else 'Unknown'}")
except ImportError as e:
    print(f"✗ Failed to import google-genai: {e}")
    sys.exit(1)

# Test 3: Try creating client
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
    print(f"✓ Client created successfully")
except Exception as e:
    print(f"✗ Failed to create client: {e}")
    sys.exit(1)

# Test 4: Try listing models
try:
    print("\nAttempting to list available models...")
    models = client.models.list()
    print("✓ Available models:")
    for model in models:
        print(f"  - {model.name}")
except Exception as e:
    print(f"✗ Failed to list models: {e}")
    print("\nTrying alternative SDK (google.generativeai)...")
    
    # Try the older SDK
    try:
        import google.generativeai as genai_alt
        genai_alt.configure(api_key=GEMINI_API_KEY)
        print("✓ Configured with google.generativeai")
        
        models = genai_alt.list_models()
        print("✓ Available models:")
        for model in models:
            print(f"  - {model.name}")
    except Exception as e2:
        print(f"✗ Also failed with google.generativeai: {e2}")
