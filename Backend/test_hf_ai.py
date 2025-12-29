"""
Test the new Hugging Face-based AI service
"""
from app.services.gemini_ai import generate_summary, generate_qa_pairs, generate_podcast_script
import os

print("Testing Hugging Face AI Service\n")
print("=" * 50)

# Find a test PDF
test_pdf = None
pdf_dir = "static/pdfs"

if os.path.exists(pdf_dir):
    pdfs = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    if pdfs:
        test_pdf = os.path.join(pdf_dir, pdfs[0])
        print(f"✓ Found test PDF: {pdfs[0]}\n")

if not test_pdf or not os.path.exists(test_pdf):
    print("❌ No PDF found in static/pdfs/")
    print("Please upload a book first through the admin dashboard")
    exit(1)

# Test Summary Generation
print("\n1. Testing Summary Generation...")
print("-" * 50)
try:
    summary = generate_summary(test_pdf)
    print(f"✅ Summary generated successfully!")
    print(f"Length: {len(summary)} characters")
    print(f"\nFirst 200 chars:\n{summary[:200]}...\n")
except Exception as e:
    print(f"❌ Summary generation failed: {str(e)}\n")

# Test Q&A Generation  
print("\n2. Testing Q&A Generation...")
print("-" * 50)
try:
    qa = generate_qa_pairs(test_pdf, num_questions=5)
    print(f"✅ Q&A generated successfully!")
    print(f"Length: {len(qa)} characters")
    print(f"\nFirst 200 chars:\n{qa[:200]}...\n")
except Exception as e:
    print(f"❌ Q&A generation failed: {str(e)}\n")

# Test Podcast Generation
print("\n3. Testing Podcast Script Generation...")
print("-" * 50)
try:
    podcast = generate_podcast_script(test_pdf)
    print(f"✅ Podcast script generated successfully!")
    print(f"Length: {len(podcast)} characters")
    print(f"\nFirst 200 chars:\n{podcast[:200]}...\n")
except Exception as e:
    print(f"❌ Podcast generation failed: {str(e)}\n")

print("\n" + "=" * 50)
print("✅ Testing complete!")
