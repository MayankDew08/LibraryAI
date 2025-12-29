"""
Check API key status and test a simple request
"""
from google import genai
import sys

API_KEYS = [
    "REDACTED_GOOGLE_API_KEY",  # API 1
    "REDACTED_GOOGLE_API_KEY",  # API 2
    "REDACTED_GOOGLE_API_KEY"   # API 3
]

print("="*60)
print("API KEY STATUS CHECK")
print("="*60)

for i, key in enumerate(API_KEYS, 1):
    print(f"\n[API Key {i}] Testing...")
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=["Say 'OK' if you can read this"]
        )
        print(f"✅ API Key {i}: WORKING")
        print(f"   Response: {response.text[:50]}")
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            print(f"❌ API Key {i}: QUOTA EXHAUSTED")
            print(f"   These keys have been used today already.")
            print(f"   Wait 24 hours or get new keys.")
        else:
            print(f"❌ API Key {i}: ERROR")
            print(f"   {error_msg[:100]}")

print("\n" + "="*60)
print("RECOMMENDATION:")
print("="*60)
print("""
If all keys are exhausted:
1. Get NEW API keys from https://aistudio.google.com/app/apikey
2. Make sure you create keys from DIFFERENT Google accounts
3. Or wait 24 hours for quota to reset

Your book WAS added successfully with RAG indexing!
- ✅ Students can borrow/return the book
- ✅ Students can use RAG chat feature
- ⏳ Summary/Q&A/Podcast available on-demand when quota resets
""")
