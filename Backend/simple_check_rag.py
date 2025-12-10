"""Simple check for RAG indexed books"""
import os
from chromadb import PersistentClient

# Path to vectordb
vectorstore_path = "static/vectordb"

# Initialize ChromaDB client
client = PersistentClient(path=vectorstore_path)

# List all collections
collections = client.list_collections()

print("\n=== RAG Indexed Books ===\n")
print(f"Total collections: {len(collections)}\n")

for collection in collections:
    print(f"Collection: {collection.name}")
    count = collection.count()
    print(f"Documents: {count}")
    
    # Extract book ID from collection name (format: book_<id>)
    if collection.name.startswith("book_"):
        book_id = collection.name.replace("book_", "")
        print(f"Book ID: {book_id}")
    
    print("-" * 60)

if len(collections) == 0:
    print("❌ No books are indexed in the RAG system!")
