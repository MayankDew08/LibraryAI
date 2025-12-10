"""Direct re-index of Psychology of Money using ChromaDB"""
import fitz  # PyMuPDF
import re
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configuration
BOOK_ID = 8
PDF_PATH = "static/pdfs/1765210331.634787_the-psychology-of-money.pdf"
VECTORSTORE_PATH = "static/vectordb"

print(f"\n🔄 Re-indexing Book {BOOK_ID}: Psychology of Money")
print(f"PDF: {PDF_PATH}\n")

# Step 1: Extract text from PDF
print("📄 Extracting text from PDF...")
def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyMuPDF"""
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            full_text += f"\n\n--- Page {page_num + 1} ---\n\n{text}"
        
        doc.close()
        return full_text
    except Exception as e:
        print(f"❌ Error extracting PDF: {e}")
        return None

text = extract_text_from_pdf(PDF_PATH)
if not text:
    print("❌ Failed to extract text!")
    exit(1)

print(f"✅ Extracted {len(text)} characters")

# Step 2: Clean text
print("\n🧹 Cleaning text...")
def clean_text(text):
    """Remove noise from PDF text"""
    # Remove common header/footer patterns
    text = re.sub(r'(Chapter|Section)\s*\d+.*?\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Page\s*\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\d+\s*/\s*\d+', '', text)
    
    # Remove metadata noise
    text = re.sub(r'©.*?\d{4}', '', text)
    text = re.sub(r'ISBN.*?\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\S+@\S+', '', text)
    
    # Clean extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()

cleaned_text = clean_text(text)
print(f"✅ Cleaned to {len(cleaned_text)} characters")

# Step 3: Split into chunks
print("\n✂️ Splitting into chunks...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""]
)

chunks = text_splitter.split_text(cleaned_text)
print(f"✅ Created {len(chunks)} chunks")

if len(chunks) == 0:
    print("❌ No chunks created! PDF might be empty or unreadable.")
    exit(1)

# Step 4: Initialize ChromaDB
print("\n💾 Initializing ChromaDB...")
client = PersistentClient(path=VECTORSTORE_PATH)

# Use Google Generative AI embeddings
embedding_function = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
    api_key="REDACTED_GOOGLE_API_KEY"
)

collection_name = f"book_{BOOK_ID}"

# Delete existing collection if it exists
try:
    client.delete_collection(collection_name)
    print(f"🗑️ Deleted existing collection: {collection_name}")
except:
    pass

# Create new collection
collection = client.create_collection(
    name=collection_name,
    embedding_function=embedding_function,
    metadata={"book_id": str(BOOK_ID)}
)

print(f"✅ Created collection: {collection_name}")

# Step 5: Add chunks to collection
print(f"\n📥 Adding {len(chunks)} chunks to collection...")

# Prepare documents
documents = chunks
ids = [f"chunk_{i}" for i in range(len(chunks))]
metadatas = [{"chunk_index": i, "book_id": BOOK_ID} for i in range(len(chunks))]

# Add in batches to avoid memory issues
batch_size = 100
for i in range(0, len(documents), batch_size):
    batch_docs = documents[i:i+batch_size]
    batch_ids = ids[i:i+batch_size]
    batch_metas = metadatas[i:i+batch_size]
    
    collection.add(
        documents=batch_docs,
        ids=batch_ids,
        metadatas=batch_metas
    )
    print(f"   Added batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")

print(f"\n✅ Successfully indexed {len(chunks)} chunks!")
print(f"   Collection: {collection_name}")
print(f"   Total documents in collection: {collection.count()}")
print("\n🎉 Psychology of Money is now fully indexed and ready for RAG queries!")
