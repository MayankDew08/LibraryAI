"""
Test script for Hugging Face AI integration
"""
import sys
sys.path.append('.')

from app.services.gemini_ai import generate_with_hf

print("Testing Hugging Face AI with token...\n")

test_prompt = "Write a short summary about the importance of reading books in 2-3 sentences."

try:
    print("Generating response...")
    response = generate_with_hf(test_prompt, max_tokens=200)
    print(f"\n✅ SUCCESS!")
    print(f"\nResponse:\n{response}")
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
