"""Re-index Psychology of Money book"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import rag_service

book_id = 8
pdf_path = "static/pdfs/1765210331.634787_the-psychology-of-money.pdf"

print(f"\n🔄 Re-indexing book {book_id}: Psychology of Money")
print(f"PDF: {pdf_path}\n")

# Delete existing index
print("Deleting existing index...")
delete_result = rag_service.delete_book_index(book_id)
if delete_result["success"]:
    print(f"✅ {delete_result['message']}")
else:
    print(f"⚠️ {delete_result.get('error', 'Could not delete')}")

# Re-index the book
print("\nIndexing PDF...")
result = rag_service.process_pdf(book_id, pdf_path)

if result["success"]:
    print(f"\n✅ Successfully indexed!")
    print(f"   Chunks created: {result['num_chunks']}")
    print(f"   Collection: {result['collection_name']}")
    print(f"   Message: {result['message']}")
else:
    print(f"\n❌ Indexing failed!")
    print(f"   Error: {result['error']}")
