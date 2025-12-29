"""
AI service for generating book summaries, Q&A, and podcast scripts
Now using Hugging Face Inference API for unlimited free access
"""
from huggingface_hub import InferenceClient
import json
from typing import Dict, Any
import os
import time
import PyPDF2

# Initialize Hugging Face Inference Client (no API key needed for public models)
# Using Meta's Llama models which are free and powerful
hf_client = InferenceClient()

# Model selection - using fast, capable models
MODEL = "meta-llama/Llama-3.2-3B-Instruct"  # Free, fast, and good quality

print(f"✓ Initialized Hugging Face AI client with model: {MODEL}")


def get_next_client():
    """Round-robin client selection for load balancing, skipping exhausted keys"""
    global current_client_index
    
    # If all keys exhausted, reset and try again
    if len(exhausted_keys) >= len(clients):
        exhausted_keys.clear()
        print("All keys exhausted, clearing exhaustion tracking and retrying")
    
    # Find next non-exhausted client
    attempts = 0
    while attempts < len(clients):
        if current_client_index not in exhausted_keys:
            client = clients[current_client_index]
            idx = current_client_index
            current_client_index = (current_client_index + 1) % len(clients)
            return client, idx
        current_client_index = (current_client_index + 1) % len(clients)
        attempts += 1
    
    # If all are exhausted, return first one anyway
    idx = 0
    current_client_index = 1
    return clients[0], idx


def mark_key_exhausted(key_index: int):
    """Mark a key as exhausted when it hits rate limit"""
    global exhausted_keys
    exhausted_keys.add(key_index)
    print(f"Marked key {key_index} as exhausted. Exhausted keys: {exhausted_keys}")


def upload_pdf_to_gemini(pdf_path: str, client=None, max_retries: int = 3):
    """Upload PDF to Gemini and return file handle with retry logic"""
    if client is None:
        client, _ = get_next_client()
    
    # If client is a tuple, extract just the client
    if isinstance(client, tuple):
        client, _ = client
    
    for attempt in range(max_retries):
        try:
            if not os.path.exists(pdf_path):
                raise ValueError(f"PDF file not found at {pdf_path}")
            
            # Upload PDF file to Gemini
            uploaded_file = client.files.upload(file=pdf_path)
            return uploaded_file
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                client, _ = get_next_client()  # Try different client
                continue
            raise ValueError(f"Error uploading PDF to Gemini: {str(e)}")
    return None


def cleanup_uploaded_file(uploaded_file, client=None):
    """Clean up uploaded file from Gemini"""
    if client is None:
        client, _ = get_next_client()
    # If client is a tuple, extract just the client
    if isinstance(client, tuple):
        client, _ = client
    try:
        if uploaded_file and uploaded_file.name:
            client.files.delete(name=uploaded_file.name)
    except Exception as e:
        print(f"Warning: Could not delete uploaded file: {e}")


def generate_summary(pdf_path: str, max_retries: int = 3) -> str:
    """Generate a comprehensive summary of the book using Gemini with retry logic"""
    uploaded_file = None
    client = None
    client_idx = None
    
    for attempt in range(max_retries):
        try:
            # Get next client (rotates through API keys)
            client, client_idx = get_next_client()
            
            # Upload PDF to Gemini
            uploaded_file = upload_pdf_to_gemini(pdf_path, client)
            
            # Generate summary with detailed prompt
            response = client.models.generate_content(
                model=MODELS["summary"],
                contents=[
                    uploaded_file,
                    """You are given a PDF document. Your task is to create a complete, detailed, and self-contained summary of this document so that the reader does not need to open or read the original file. 

Capture all key points, arguments, data, examples, and conclusions. Structure the summary with clear sections (e.g., Introduction, Main Ideas, Evidence/Details, and Conclusion). 

Rewrite in clear, simple language while preserving the meaning and depth of the original. Do not skip important details. The summary should be the only source the user needs to fully understand the document."""
                ]
            )
            
            if not response.text:
                raise ValueError("Empty response from Gemini AI")
            
            return response.text
        except Exception as e:
            error_msg = str(e)
            if attempt < max_retries - 1:
                if uploaded_file:
                    cleanup_uploaded_file(uploaded_file, client)
                    uploaded_file = None
                # Handle rate limit - switch to next key immediately
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    print(f"Rate limit hit on key {current_client_index}, switching to next key (retry {attempt + 1}/{max_retries})")
                    # Don't wait - just switch to next key and retry immediately
                else:
                    time.sleep(2 ** attempt)
                continue
            raise ValueError(f"Error generating summary: {str(e)}")
        finally:
            # Clean up uploaded file
            if uploaded_file and client:
                cleanup_uploaded_file(uploaded_file, client)
    
    raise ValueError("Failed to generate summary after all retries")


def generate_qa_pairs(pdf_path: str, num_questions: int = 10, max_retries: int = 3) -> str:
    """Generate Q&A pairs from the book content using Gemini with retry logic"""
    uploaded_file = None
    client = None
    client_idx = None
    
    for attempt in range(max_retries):
        try:
            client, client_idx = get_next_client()
            
            # Upload PDF to Gemini
            uploaded_file = upload_pdf_to_gemini(pdf_path, client)
            
            # Generate Q&A with structured prompt
            prompt = f"""You are given a PDF document. Your task is to create a complete, detailed, and self-contained Q&A of this document so that the reader does not need to open or read the original file. 

Generate {num_questions} important question-answer pairs that cover:
1. Key concepts and definitions
2. Important facts and information  
3. Critical thinking questions
4. Application-based questions

Capture all key points, arguments, data, examples, and conclusions. Structure the Q&A with clear sections (e.g., Introduction, Main Ideas, Evidence/Details, and Conclusion). 

Rewrite in clear, simple language while preserving the meaning and depth of the original. Do not skip important details. The Q&A should be the only source the user needs to fully understand the document.

Return the response as a valid JSON array in this exact format:
[
    {{"question": "question text here", "answer": "answer text here"}},
    ...
]

Ensure the JSON is properly formatted and valid."""
            
            response = client.models.generate_content(
                model=MODELS["qa"],
                contents=[uploaded_file, prompt]
            )
            
            if not response.text:
                raise ValueError("Empty response from Gemini AI")
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()
            
            # Validate JSON
            json.loads(response_text)  # This will raise an error if invalid
            
            return response_text
        except (json.JSONDecodeError, Exception) as e:
            error_msg = str(e)
            if attempt < max_retries - 1:
                if uploaded_file:
                    cleanup_uploaded_file(uploaded_file, client)
                    uploaded_file = None
                # Handle rate limit - mark key as exhausted and switch
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    if client_idx is not None:
                        mark_key_exhausted(client_idx)
                    print(f"Rate limit hit, switching to next available key (retry {attempt + 1}/{max_retries})")
                    # Don't wait - just switch to next key and retry immediately
                else:
                    time.sleep(2 ** attempt)
                continue
            if isinstance(e, json.JSONDecodeError):
                raise ValueError(f"Error parsing Q&A JSON: {str(e)}")
            raise ValueError(f"Error generating Q&A: {str(e)}")
        finally:
            # Clean up uploaded file
            if uploaded_file and client:
                cleanup_uploaded_file(uploaded_file, client)
    
    raise ValueError("Failed to generate Q&A after all retries")


def generate_podcast_script(pdf_path: str, max_retries: int = 3) -> str:
    """Generate an engaging podcast transcript using Gemini with retry logic"""
    uploaded_file = None
    client = None
    client_idx = None
    
    for attempt in range(max_retries):
        try:
            client, client_idx = get_next_client()
            
            # Upload PDF to Gemini
            uploaded_file = upload_pdf_to_gemini(pdf_path, client)
            
            # Generate podcast transcript with engaging prompt
            response = client.models.generate_content(
                model=MODELS["podcast"],
                contents=[
                    uploaded_file,
                    """You are creating a podcast-style audio script from a PDF document. This script will be read aloud by a text-to-speech system, so format it accordingly.

CRITICAL REQUIREMENTS:
1. Write ONLY plain text - no markdown, no asterisks, no hashtags, no special formatting characters
2. Do NOT use Speaker1, Speaker2, or any speaker labels
3. Write as continuous flowing narration in simple, conversational language
4. Use commas for short pauses, semicolons for medium pauses, and periods for full stops
5. Use "and" to connect ideas smoothly
6. Break complex sentences into shorter ones for better speech flow
7. Use natural transitions like "Now," "Next," "Moving on," "Importantly,"

CONTENT STRUCTURE:
- Start with a brief, engaging introduction to the topic
- Cover all key points, arguments, data, examples, and conclusions from the document
- Use clear, simple language that sounds natural when spoken aloud
- Organize ideas logically with smooth transitions between topics
- End with a brief conclusion summarizing the main takeaways

TONE: Conversational, engaging, educational - as if explaining to a friend

Remember: This will be converted to speech, so write exactly what should be spoken, with no formatting marks or special characters. Use punctuation strategically to create natural pauses and emphasis."""
                ]
            )
            
            if not response.text:
                raise ValueError("Empty response from Gemini AI")
            
            return response.text
        except Exception as e:
            error_msg = str(e)
            if attempt < max_retries - 1:
                if uploaded_file:
                    cleanup_uploaded_file(uploaded_file, client)
                    uploaded_file = None
                # Handle rate limit - mark key as exhausted and switch
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    if client_idx is not None:
                        mark_key_exhausted(client_idx)
                    print(f"Rate limit hit, switching to next available key (retry {attempt + 1}/{max_retries})")
                    # Don't wait - just switch to next key and retry immediately
                else:
                    time.sleep(2 ** attempt)
                continue
            raise ValueError(f"Error generating podcast script: {str(e)}")
        finally:
            # Clean up uploaded file
            if uploaded_file and client:
                cleanup_uploaded_file(uploaded_file, client)
    
    raise ValueError("Failed to generate podcast script after all retries")


def generate_all_content(pdf_path: str) -> Dict[str, Any]:
    """
    Generate all content (summary, Q&A, podcast script) from a PDF using SEQUENTIAL processing
    Sequential processing prevents exhausting all API keys simultaneously
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing summary_text, qa_json, and podcast_script
    """
    try:
        print("Starting sequential content generation...")
        
        # Generate sequentially to avoid exhausting all keys at once
        print("Step 1/3: Generating summary...")
        summary_text = generate_summary(pdf_path)
        print("✓ Summary generated")
        
        print("Step 2/3: Generating Q&A...")
        qa_json = generate_qa_pairs(pdf_path, 10)
        print("✓ Q&A generated")
        
        print("Step 3/3: Generating podcast script...")
        podcast_script = generate_podcast_script(pdf_path)
        print("✓ Podcast script generated")
        
        return {
            "summary_text": summary_text,
            "qa_json": qa_json,
            "podcast_script": podcast_script
        }
    except Exception as e:
        raise ValueError(f"Error generating content: {str(e)}")
