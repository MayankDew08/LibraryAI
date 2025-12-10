"""
Audio generation service for podcast scripts using pyttsx3 (fast, offline TTS)
"""
import pyttsx3
import os
import re
from app.config.settings import AUDIO_OUTPUT_DIR
from datetime import datetime, timezone


def extract_clean_content(transcript_content: str) -> str:
    """Extract and clean content from transcript for TTS"""
    lines = transcript_content.split('\n')
    clean_content = []
    
    for line in lines:
        line = line.strip()
        
        # Skip metadata and formatting lines
        if not line or line.startswith(('PDF Transcript:', 'Generated on:', '====', '---', '###', '**(', 'This document covers')):
            continue
            
        # Process speaker lines - remove speaker markers
        if line.startswith('**Speaker1:**') or line.startswith('**Speaker2:**'):
            content = re.sub(r'\*\*Speaker[12]:\*\*\s*', '', line).strip()
            if content:
                clean_content.append(content)
        elif line and not line.startswith(('http', '[', 'mospi.gov')):
            # Clean up formatting
            clean_line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)  # Remove bold markers
            clean_line = re.sub(r'####\s*', '', clean_line)  # Remove heading markers
            clean_line = clean_line.replace('*   ', '').strip()  # Remove bullet points
            
            if clean_line and len(clean_line) > 10:  # Only include substantial content
                clean_content.append(clean_line)
    
    return ' '.join(clean_content)


def setup_tts_engine():
    """Setup TTS engine with automatic best voice selection"""
    engine = pyttsx3.init()
    
    try:
        voices = engine.getProperty('voices')
        
        if voices and len(voices) > 0:
            # Auto-select best voice (prefer male for professional podcasts)
            best_voice = None
            for voice in voices:
                try:
                    name_lower = voice.name.lower()
                    if 'david' in name_lower or 'mark' in name_lower:
                        best_voice = voice
                        break
                except:
                    continue
            
            if not best_voice:
                best_voice = voices[0]
            
            engine.setProperty('voice', best_voice.id)
        else:
            print("Warning: No voices found, using system default")
            
    except Exception as e:
        print(f"Warning: Voice setup error: {e}")
    
    # Set optimal podcast settings
    engine.setProperty('rate', 185)  # Professional pace (words per minute)
    engine.setProperty('volume', 0.9)  # Good volume level
    
    return engine


def generate_podcast_audio(script: str, book_id: int) -> str:
    """
    Generate audio file from podcast script using pyttsx3 (fast, offline TTS)
    
    Args:
        script: The podcast script text
        book_id: ID of the book for filename generation
        
    Returns:
        Path to the generated audio file
    """
    try:
        # Create audio directory if it doesn't exist
        os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)
        
        # Clean the script text
        clean_text = extract_clean_content(script)
        
        if not clean_text:
            raise ValueError("No content to convert to audio after cleaning")
        
        # Generate filename
        timestamp = datetime.now(timezone.utc).timestamp()
        filename = f"podcast_book_{book_id}_{int(timestamp)}.wav"
        audio_path = os.path.join(AUDIO_OUTPUT_DIR, filename)
        
        # Setup TTS engine
        engine = setup_tts_engine()
        
        # Generate audio using pyttsx3 (much faster than gTTS)
        engine.save_to_file(clean_text, audio_path)
        engine.runAndWait()
        
        # Verify file was created
        if not os.path.exists(audio_path):
            raise ValueError("Audio file was not created")
        
        return audio_path
        
    except Exception as e:
        raise ValueError(f"Error generating podcast audio: {str(e)}")


def delete_podcast_audio(audio_path: str) -> bool:
    """
    Delete podcast audio file
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        if os.path.exists(audio_path):
            os.remove(audio_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting audio file: {str(e)}")
        return False
