"""Test the fixed Q&A generation"""
import json
from app.services.gemini_ai import generate_qa_pairs

def test_qa_generation():
    # Test with a sample PDF
    pdf_path = "static/pdfs/PS-5.pdf"  # Adjust if needed
    
    print("Testing Q&A generation with improved prompt...")
    print("-" * 60)
    
    try:
        result = generate_qa_pairs(pdf_path, num_questions=5)
        print("\n✅ Q&A Generation Successful!")
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result)} characters")
        
        # Parse and validate JSON
        qa_pairs = json.loads(result)
        print(f"\n✅ Valid JSON with {len(qa_pairs)} Q&A pairs")
        
        # Show first 2 pairs
        print("\nSample Q&A pairs:")
        for i, pair in enumerate(qa_pairs[:2], 1):
            print(f"\nQ{i}: {pair['question']}")
            print(f"A{i}: {pair['answer'][:150]}...")
        
        print("\n" + "="*60)
        print("✅ All validations passed!")
        
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON Parse Error: {e}")
        print(f"Error at position: {e.pos}")
        if hasattr(e, 'msg'):
            print(f"Error message: {e.msg}")
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_qa_generation()
