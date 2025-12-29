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
hf_client = InferenceClient()

# Model selection - using Meta's Llama 3.2 which is free and powerful
MODEL = "meta-llama/Llama-3.2-3B-Instruct"

print(f"✓ Initialized Hugging Face AI client with model: {MODEL}")


def extract_text_from_pdf(pdf_path: str, max_pages: int = None) -> str:
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            if max_pages:
                num_pages = min(num_pages, max_pages)
            
            text = ""
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
            
            return text.strip()
    except Exception as e:
        raise ValueError(f"Error extracting text from PDF: {str(e)}")


def chunk_text(text: str, max_chunk_size: int = 8000) -> list[str]:
    """Split text into chunks for processing"""
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        word_size = len(word) + 1
        if current_size + word_size > max_chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_size = word_size
        else:
            current_chunk.append(word)
            current_size += word_size
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks


def generate_with_hf(prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
    """Generate text using Hugging Face Inference API"""
    try:
        response = hf_client.text_generation(
            prompt,
            model=MODEL,
            max_new_tokens=max_tokens,
            temperature=temperature,
            return_full_text=False
        )
        return response.strip()
    except Exception as e:
        raise ValueError(f"Error generating with Hugging Face: {str(e)}")


def generate_summary(pdf_path: str, max_retries: int = 3) -> str:
    """Generate a comprehensive summary from the book content"""
    
    for attempt in range(max_retries):
        try:
            # Extract text from PDF (limit to first 100 pages for speed)
            print(f"Extracting text from PDF (attempt {attempt + 1}/{max_retries})...")
            text = extract_text_from_pdf(pdf_path, max_pages=100)
            
            if not text or len(text) < 100:
                raise ValueError("Could not extract sufficient text from PDF")
            
            # If text is too long, chunk it and summarize chunks
            chunks = chunk_text(text, max_chunk_size=8000)
            print(f"Processing {len(chunks)} chunks...")
            
            if len(chunks) == 1:
                # Single chunk - summarize directly
                prompt = f"""You are an expert at creating comprehensive book summaries.

Read the following text and create a complete, detailed summary that captures all key points, arguments, data, examples, and conclusions.

Structure your summary with clear sections:
- Introduction
- Main Ideas
- Key Details and Evidence
- Conclusion

Write in clear, simple language while preserving the meaning and depth of the original.

Text to summarize:
{chunks[0][:8000]}

Summary:"""

                summary = generate_with_hf(prompt, max_tokens=2000)
                return summary
            else:
                # Multiple chunks - summarize each then combine
                chunk_summaries = []
                for i, chunk in enumerate(chunks[:3]):  # Limit to first 3 chunks
                    print(f"Summarizing chunk {i+1}/{min(3, len(chunks))}...")
                    prompt = f"""Summarize this section concisely, capturing the main points:

{chunk[:8000]}

Summary:"""
                    chunk_summary = generate_with_hf(prompt, max_tokens=800)
                    chunk_summaries.append(chunk_summary)
                    time.sleep(1)  # Rate limiting
                
                # Combine chunk summaries into final summary
                combined = "\n\n".join(chunk_summaries)
                final_prompt = f"""Create a comprehensive summary from these section summaries:

{combined}

Provide a well-structured final summary with Introduction, Main Ideas, Key Details, and Conclusion:"""
                
                final_summary = generate_with_hf(final_prompt, max_tokens=2000)
                return final_summary
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error on attempt {attempt + 1}: {str(e)}")
                time.sleep(2 ** attempt)
                continue
            raise ValueError(f"Error generating summary: {str(e)}")
    
    raise ValueError("Failed to generate summary after all retries")


def generate_qa_pairs(pdf_path: str, num_questions: int = 10, max_retries: int = 3) -> str:
    """Generate Q&A pairs from the book content"""
    
    for attempt in range(max_retries):
        try:
            # Extract text from PDF
            print(f"Extracting text for Q&A (attempt {attempt + 1}/{max_retries})...")
            text = extract_text_from_pdf(pdf_path, max_pages=50)
            
            if not text or len(text) < 100:
                raise ValueError("Could not extract sufficient text from PDF")
            
            # Chunk the text if needed
            chunks = chunk_text(text, max_chunk_size=8000)
            
            # Generate Q&A pairs from first chunk (most important content usually at start)
            chunk_text_sample = chunks[0][:8000]
            
            prompt = f"""You are an expert educator creating study questions.

Based on the following text, generate {num_questions} important question-answer pairs that cover:
1. Key concepts and definitions
2. Important facts and information
3. Critical thinking questions
4. Application-based questions

Return ONLY a valid JSON array in this exact format (no other text):
[
    {{"question": "What is...", "answer": "The answer is..."}},
    {{"question": "How does...", "answer": "It works by..."}}
]

Text:
{chunk_text_sample}

JSON Array:"""

            response = generate_with_hf(prompt, max_tokens=2000, temperature=0.7)
            
            # Clean up response
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith("```json"):
                response = response.replace("```json", "").replace("```", "").strip()
            elif response.startswith("```"):
                response = response.replace("```", "").strip()
            
            # Try to find JSON array in response
            if "[" in response and "]" in response:
                start = response.index("[")
                end = response.rindex("]") + 1
                response = response[start:end]
            
            # Validate JSON
            parsed = json.loads(response)
            if not isinstance(parsed, list) or len(parsed) == 0:
                raise ValueError("Invalid Q&A format")
            
            return response
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error on attempt {attempt + 1}: {str(e)}")
                time.sleep(2 ** attempt)
                continue
            raise ValueError(f"Error generating Q&A: {str(e)}")
    
    raise ValueError("Failed to generate Q&A after all retries")


def generate_podcast_script(pdf_path: str, max_retries: int = 3) -> str:
    """Generate a podcast script from the book content"""
    
    for attempt in range(max_retries):
        try:
            # Extract text from PDF
            print(f"Extracting text for podcast (attempt {attempt + 1}/{max_retries})...")
            text = extract_text_from_pdf(pdf_path, max_pages=30)
            
            if not text or len(text) < 100:
                raise ValueError("Could not extract sufficient text from PDF")
            
            # Use first chunk for podcast
            chunks = chunk_text(text, max_chunk_size=6000)
            chunk_sample = chunks[0][:6000]
            
            prompt = f"""You are a podcast script writer. Create an engaging 2-person podcast dialogue about this book.

Guidelines:
- Host introduces the topic
- Guest (expert) explains key concepts
- Natural, conversational tone
- Include interesting examples
- End with key takeaways
- Length: 500-800 words

Format:
Host: [dialogue]
Guest: [dialogue]

Book content:
{chunk_sample}

Podcast Script:"""

            script = generate_with_hf(prompt, max_tokens=1500, temperature=0.8)
            
            if not script or len(script) < 100:
                raise ValueError("Generated script too short")
            
            return script
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error on attempt {attempt + 1}: {str(e)}")
                time.sleep(2 ** attempt)
                continue
            raise ValueError(f"Error generating podcast script: {str(e)}")
    
    raise ValueError("Failed to generate podcast script after all retries")
