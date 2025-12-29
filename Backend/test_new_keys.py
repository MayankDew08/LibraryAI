"""
Quick test script to verify which API keys are working
"""
from google import genai
import time

API_KEYS = [
    "REDACTED_GOOGLE_API_KEY",
    "REDACTED_GOOGLE_API_KEY",
    "REDACTED_GOOGLE_API_KEY"
]

print("Testing API Keys...\n")

for i, key in enumerate(API_KEYS, 1):
    print(f"Testing Key {i}: {key[:20]}...")
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents="Say 'Hello, I am working!'"
        )
        print(f"✅ Key {i} WORKS: {response.text[:50]}")
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            print(f"❌ Key {i} EXHAUSTED: Rate limit hit")
        elif "API_KEY_INVALID" in error_msg:
            print(f"❌ Key {i} INVALID: Check the key")
        else:
            print(f"❌ Key {i} ERROR: {error_msg[:100]}")
    
    time.sleep(2)  # Wait between tests

print("\n✅ Test complete!")
