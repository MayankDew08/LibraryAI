"""
AI service for generating book summaries, Q&A, and podcast scripts
Using Hugging Face Inference API with Meta Llama 3.2 model
"""
from huggingface_hub import InferenceClient
from app.config.settings import HUGGINGFACE_API_TOKEN
import json
from typing import Dict, Any
import os
import time
import PyPDF2

# Initialize Hugging Face Inference Client with API token
# Using Meta Llama 3.2-3B-Instruct - free, fast, excellent for instruction following
hf_client = InferenceClient(
    token=HUGGINGFACE_API_TOKEN
)

# Using Llama 3.2-3B for all tasks - free, powerful, and uses chat completion API
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


def generate_with_hf(prompt: str, max_tokens: int = 4000, temperature: float = 0.7, max_retries: int = 3) -> str:
    """Generate text using Hugging Face Inference API with chat completion"""
    
    for retry in range(max_retries):
        try:
            # Use chat completion API for Llama models
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = hf_client.chat_completion(
                messages=messages,
                model=MODEL,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    return content.strip()
                else:
                    raise ValueError("Empty content in response")
            else:
                raise ValueError("Empty response from Hugging Face")
                
        except Exception as e:
            error_str = str(e)
            
            # Retry on errors
            if retry < max_retries - 1:
                print(f"Error on retry {retry + 1}/{max_retries}: {error_str[:100]}")
                time.sleep(2 ** retry)
                continue
            else:
                raise ValueError(f"Error generating with Hugging Face: {error_str}")
    
    raise ValueError("Failed to generate content after all retries")


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
                prompt = f"""You are an expert at creating detailed, comprehensive book summaries with moderate depth.

Analyze the following text carefully and create a thorough summary that:

1. Captures ALL main concepts, theories, and ideas presented
2. Includes specific examples, data points, and case studies mentioned
3. Explains the reasoning and logic behind key arguments
4. Highlights important definitions and terminology
5. Shows relationships between different concepts
6. Preserves the author's insights and conclusions

Structure your summary with these sections:

**Overview**
Brief introduction to the topic and scope

**Main Concepts**
Detailed explanation of core ideas with examples

**Key Details**
Important facts, data, research findings, and supporting evidence

**Practical Applications**
How the concepts can be applied or used

**Conclusion**
Main takeaways and final thoughts

Write in clear, engaging language. Make it informative yet accessible. Aim for moderate depth - not too shallow, not overly technical.

Text to summarize:
{chunks[0][:8000]}

Provide your detailed summary:"""

                summary = generate_with_hf(prompt, max_tokens=3000)
                return summary
            else:
                # Multiple chunks - summarize each then combine
                chunk_summaries = []
                for i, chunk in enumerate(chunks[:3]):  # Limit to first 3 chunks
                    print(f"Summarizing chunk {i+1}/{min(3, len(chunks))}...")
                    prompt = f"""Summarize this section in detail, capturing:
- All main points and concepts
- Key examples and evidence
- Important definitions and terms
- Logical connections between ideas

Text:
{chunk[:8000]}

Detailed summary:"""
                    chunk_summary = generate_with_hf(prompt, max_tokens=1000)
                    chunk_summaries.append(chunk_summary)
                    time.sleep(1)  # Rate limiting
                
                # Combine chunk summaries into final summary
                combined = "\n\n".join(chunk_summaries)
                final_prompt = f"""You have summaries from different sections of a book. Create one comprehensive, unified summary that:

1. Integrates all key concepts from each section
2. Shows how ideas connect across sections
3. Maintains moderate depth with specific details
4. Includes examples and evidence mentioned
5. Preserves important terminology

Section summaries:
{combined}

Structure your final summary with:
**Overview**, **Main Concepts**, **Key Details**, **Practical Applications**, **Conclusion**

Provide your comprehensive, well-integrated summary:"""
                
                final_summary = generate_with_hf(final_prompt, max_tokens=3000)
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
            chunk_text_sample = chunks[0][:5000]
            
            # Generate one Q&A at a time for reliability
            qa_pairs = []
            for i in range(min(num_questions, 10)):
                try:
                    prompt = f"""Based on this text, generate 1 question and answer.

Text:
{chunk_text_sample}

Output format (JSON object only, no extra text):
{{"question": "Your question here?", "answer": "Your answer in 2-3 sentences."}}

Generate the JSON now:"""

                    response = generate_with_hf(prompt, max_tokens=300, temperature=0.3)
                    response = response.strip()
                    
                    # Clean response
                    if "```json" in response:
                        response = response.split("```json")[1].split("```")[0].strip()
                    elif "```" in response:
                        response = response.split("```")[1].split("```")[0].strip()
                    
                    # Extract JSON object
                    if "{" in response and "}" in response:
                        start = response.index("{")
                        end = response.rindex("}") + 1
                        response = response[start:end]
                    
                    # Clean problematic characters
                    response = response.replace('\n', ' ').replace('\r', ' ')
                    response = response.replace('\t', ' ')
                    
                    # Parse
                    pair = json.loads(response)
                    
                    # Validate structure
                    if isinstance(pair, dict) and 'question' in pair and 'answer' in pair:
                        # Clean the values
                        pair['question'] = pair['question'].strip()
                        pair['answer'] = pair['answer'].strip()
                        qa_pairs.append(pair)
                        print(f"Generated Q&A {len(qa_pairs)}/{num_questions}")
                        
                        if len(qa_pairs) >= num_questions:
                            break
                    
                    time.sleep(0.5)  # Small delay between generations
                    
                except Exception as e:
                    print(f"Failed to generate Q&A {i+1}: {str(e)}")
                    continue
            
            if len(qa_pairs) == 0:
                raise ValueError("Could not generate any Q&A pairs")
            
            return json.dumps(qa_pairs, ensure_ascii=False)
            
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
            
            prompt = f"""You are a professional podcast script writer. Create an engaging, story-like single-speaker podcast script about this book.

CRITICAL FORMAT RULES:
- This is a SINGLE-SPEAKER podcast (one narrator only)
- Use ONLY plain text - NO special characters, NO markdown, NO asterisks, NO bullet points
- NO "Host:", NO "Guest:", NO labels - just the continuous script
- Write as if speaking directly to the listener
- Natural, conversational tone like telling a story to a friend

Content Structure (include all components):
1. **Opening Hook** - Start with an engaging question, surprising fact, or relatable scenario that grabs attention
2. **Introduction** - Briefly introduce the topic and why it matters
3. **Main Content** - Tell the story of the key concepts:
   - Explain ideas clearly with real-world examples
   - Use analogies and metaphors to make complex ideas simple
   - Share interesting details, anecdotes, and insights from the text
   - Build excitement and curiosity as you go
   - Show WHY concepts matter and HOW they apply to real life
4. **Practical Applications** - Give listeners actionable takeaways
5. **Memorable Closing** - End with a powerful summary or call-to-action

Writing Style:
- Warm, enthusiastic, story-like, educational but entertaining
- Speak conversationally using "you" and "we"
- Use transitions like "Now...", "Here's the thing...", "But wait...", "And this is important..."
- Make it sound like a friendly conversation, not a lecture
- Length: 600-900 words for moderate depth

Book content:
{chunk_sample}

Write the complete single-speaker podcast script now (plain text only, no formatting, no labels):"""

            script = generate_with_hf(prompt, max_tokens=2000, temperature=0.8)
            
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


def generate_all_content(pdf_path: str) -> Dict[str, Any]:
    """
    Generate all static content (summary, Q&A, podcast script) from PDF
    This is the main orchestrator function called by the API
    """
    try:
        print(f"\n{'='*60}")
        print(f"Starting sequential content generation for: {pdf_path}")
        print(f"{'='*60}\n")
        
        results = {}
        
        # Step 1: Generate Summary
        print("Step 1/3: Generating summary...")
        try:
            summary = generate_summary(pdf_path)
            results["summary_text"] = summary
            print(f"✓ Summary generated successfully ({len(summary)} characters)")
        except Exception as e:
            print(f"✗ Summary generation failed: {str(e)}")
            results["summary_text"] = None
            results["summary_error"] = str(e)
        
        time.sleep(2)  # Brief pause between generations
        
        # Step 2: Generate Q&A
        print("\nStep 2/3: Generating Q&A pairs...")
        try:
            qa_json = generate_qa_pairs(pdf_path, num_questions=10)
            results["qa_json"] = qa_json
            print(f"✓ Q&A generated successfully")
        except Exception as e:
            print(f"✗ Q&A generation failed: {str(e)}")
            results["qa_json"] = None
            results["qa_error"] = str(e)
        
        time.sleep(2)  # Brief pause between generations
        
        # Step 3: Generate Podcast Script
        print("\nStep 3/3: Generating podcast script...")
        try:
            podcast_script = generate_podcast_script(pdf_path)
            results["podcast_script"] = podcast_script
            print(f"✓ Podcast script generated successfully ({len(podcast_script)} characters)")
        except Exception as e:
            print(f"✗ Podcast generation failed: {str(e)}")
            results["podcast_script"] = None
            results["podcast_error"] = str(e)
        
        print(f"\n{'='*60}")
        print(f"Content generation complete!")
        print(f"{'='*60}\n")
        
        # Check if at least one content type was generated successfully
        if not any([results.get("summary_text"), results.get("qa_json"), results.get("podcast_script")]):
            raise ValueError("All content generation failed. Please check API quota and try again.")
        
        return results
        
    except Exception as e:
        raise ValueError(f"Error in content generation pipeline: {str(e)}")
