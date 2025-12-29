"""
Test improved prompts with Hugging Face
"""
from huggingface_hub import InferenceClient
from app.config.settings import HUGGINGFACE_API_TOKEN

print("Testing improved prompts with Llama 3.2...\n")

client = InferenceClient(token=HUGGINGFACE_API_TOKEN)
MODEL = "meta-llama/Llama-3.2-3B-Instruct"

# Test podcast generation with new prompt
test_content = """
Python is a high-level programming language known for its simplicity and readability. 
It was created by Guido van Rossum and first released in 1991. Python supports multiple 
programming paradigms including procedural, object-oriented, and functional programming.
Key features include dynamic typing, automatic memory management, and a large standard library.
Python is widely used in web development, data science, artificial intelligence, and automation.
"""

prompt = f"""You are a professional podcast script writer. Create an engaging, story-like single-speaker podcast script about this book.

CRITICAL FORMAT RULES:
- This is a SINGLE-SPEAKER podcast (one narrator only)
- Use ONLY plain text - NO special characters, NO markdown, NO asterisks, NO bullet points
- NO "Host:", NO "Guest:", NO labels - just the continuous script
- Write as if speaking directly to the listener
- Natural, conversational tone like telling a story to a friend

Content Structure (include all components):
1. **Opening Hook** - Start with an engaging question, surprising fact, or relatable scenario
2. **Introduction** - Briefly introduce the topic and why it matters
3. **Main Content** - Tell the story of the key concepts with real examples and analogies
4. **Practical Applications** - Give listeners actionable takeaways
5. **Memorable Closing** - End with a powerful summary

Writing Style:
- Warm, enthusiastic, story-like, educational but entertaining
- Speak conversationally using "you" and "we"
- Use transitions like "Now...", "Here's the thing...", "But wait..."
- Length: 400-500 words

Book content:
{test_content}

Write the complete single-speaker podcast script now (plain text only, no formatting, no labels):"""

try:
    messages = [{"role": "user", "content": prompt}]
    
    print("Generating podcast script...")
    response = client.chat_completion(
        messages=messages,
        model=MODEL,
        max_tokens=1000,
        temperature=0.8
    )
    
    script = response.choices[0].message.content
    
    print("\n✅ SUCCESS! Generated podcast script:\n")
    print("="*60)
    print(script)
    print("="*60)
    
    # Check format - should be single speaker (no Host:/Guest: labels)
    if script:
        if "Host:" not in script and "Guest:" not in script:
            print("\n✅ Format looks good - Single speaker podcast!")
        else:
            print("\n⚠️ Warning: Found Host/Guest labels (should be single speaker)")
    else:
        print("\n⚠️ Warning: Empty script")
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
