"""
Quick test to verify RAG indexing is working with the Theory of Fun book
"""
from app.services.rag_service import rag_service
import os

# Test with the Theory of Fun PDF that was failing
pdf_path = "static/pdfs/1765428714.109551_Theory_of_fun.pdf"
book_id = 11

print("="*60)
print("Testing RAG Indexing Fix")
print("="*60)
print(f"\nPDF: {pdf_path}")
print(f"Book ID: {book_id}")
print(f"File exists: {os.path.exists(pdf_path)}")
print("\nStarting RAG indexing test...\n")

try:
    result = rag_service.process_pdf(pdf_path, book_id)
    
    print("\n" + "="*60)
    print("RESULT:")
    print("="*60)
    
    if result.get("success"):
        print("✅ RAG INDEXING SUCCESSFUL!")
        print(f"   Total pages: {result.get('total_pages')}")
        print(f"   Total chunks: {result.get('total_chunks')}")
        print(f"   Unique chunks: {result.get('unique_chunks')}")
        print(f"   Deduplication: {result.get('deduplication_percentage')}%")
        print(f"   Collection: {result.get('collection_name')}")
    else:
        print("❌ RAG INDEXING FAILED!")
        print(f"   Error: {result.get('error')}")
        
except Exception as e:
    print("❌ EXCEPTION OCCURRED!")
    print(f"   Error: {str(e)}")
    import traceback
    traceback.print_exc()
