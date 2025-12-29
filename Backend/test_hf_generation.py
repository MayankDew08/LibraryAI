"""
Test Hugging Face AI generation
"""
from huggingface_hub import InferenceClient
from app.config.settings import HUGGINGFACE_API_TOKEN

print("Testing Hugging Face Inference API...\n")

try:
    client = InferenceClient(token=HUGGINGFACE_API_TOKEN)
    
    MODEL = "meta-llama/Llama-3.2-3B-Instruct"
    
    messages = [
        {
            "role": "user",
            "content": "Generate a short summary (2-3 sentences) about Python programming language."
        }
    ]
    
    print(f"Using model: {MODEL}")
    print("Generating with chat completion...")
    
    response = client.chat_completion(
        messages=messages,
        model=MODEL,
        max_tokens=200,
        temperature=0.7
    )
    
    print(f"\n✅ SUCCESS!\n")
    print(f"Response:\n{response.choices[0].message.content}")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
