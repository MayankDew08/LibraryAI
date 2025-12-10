"""
Gemini AI service for generating book summaries, Q&A, and podcast scripts
Uses Google GenAI SDK (google-genai) with multiple API keys and parallel processing
"""
from google import genai
from app.config.settings import GEMINI_API_KEY
import json
from typing import Dict, Any
import os
import time
from concurrent.futures import ThreadPoolExecutor


# Multiple API keys for load balancing (add more if needed)
API_KEYS = [
    GEMINI_API_KEY,
    # Add more API keys here if available
]

# Different models to distribute the load
# Using only gemini-2.5-flash to avoid quota issues with other models
MODELS = {
    "summary": "models/gemini-2.5-flash",
    "qa": "models/gemini-2.5-flash",  
    "podcast": "models/gemini-2.5-flash"
}

# Create multiple clients for parallel processing
clients = [genai.Client(api_key=key) for key in API_KEYS]
current_client_index = 0


def get_next_client():
    """Round-robin client selection for load balancing"""
    global current_client_index
    client = clients[current_client_index]
    current_client_index = (current_client_index + 1) % len(clients)
    return client


def upload_pdf_to_gemini(pdf_path: str, client=None, max_retries: int = 3):
    """Upload PDF to Gemini and return file handle with retry logic"""
    if client is None:
        client = get_next_client()
    
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
                client = get_next_client()  # Try different client
                continue
            raise ValueError(f"Error uploading PDF to Gemini: {str(e)}")
    return None


def cleanup_uploaded_file(uploaded_file, client=None):
    """Clean up uploaded file from Gemini"""
    if client is None:
        client = get_next_client()
    try:
        if uploaded_file and uploaded_file.name:
            client.files.delete(name=uploaded_file.name)
    except Exception as e:
        print(f"Warning: Could not delete uploaded file: {e}")


def generate_summary(pdf_path: str, max_retries: int = 3) -> str:
    """Generate a comprehensive summary of the book using Gemini with retry logic"""
    uploaded_file = None
    client = None
    
    for attempt in range(max_retries):
        try:
            client = get_next_client()
            
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
            if attempt < max_retries - 1:
                if uploaded_file:
                    cleanup_uploaded_file(uploaded_file, client)
                    uploaded_file = None
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
    
    for attempt in range(max_retries):
        try:
            client = get_next_client()
            
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
            if attempt < max_retries - 1:
                if uploaded_file:
                    cleanup_uploaded_file(uploaded_file, client)
                    uploaded_file = None
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
    
    for attempt in range(max_retries):
        try:
            client = get_next_client()
            
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
            if attempt < max_retries - 1:
                if uploaded_file:
                    cleanup_uploaded_file(uploaded_file, client)
                    uploaded_file = None
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
    Generate all content (summary, Q&A, podcast script) from a PDF using parallel processing
    Uses different models and API keys to distribute load
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing summary_text, qa_json, and podcast_script
    """
    try:
        # Use ThreadPoolExecutor for parallel API calls
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all tasks in parallel to different models/clients
            summary_future = executor.submit(generate_summary, pdf_path)
            qa_future = executor.submit(generate_qa_pairs, pdf_path, 10)
            podcast_future = executor.submit(generate_podcast_script, pdf_path)
            
            # Wait for all tasks to complete and get results
            summary_text = summary_future.result()
            qa_json = qa_future.result()
            podcast_script = podcast_future.result()
        
        return {
            "summary_text": summary_text,
            "qa_json": qa_json,
            "podcast_script": podcast_script
        }
    except Exception as e:
        raise ValueError(f"Error generating content: {str(e)}")
