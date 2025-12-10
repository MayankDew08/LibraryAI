"""
RAG Service for Library Management System
Handles PDF preprocessing, vector storage, and intelligent Q&A
"""

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from difflib import SequenceMatcher
import re
import os
from typing import Dict, List


class RAGService:
    """RAG Service for intelligent document Q&A"""
    
    def __init__(self):
        # Local embeddings (free, fast, private)
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Vector store directory
        self.vectorstore_path = "static/vectordb"
        os.makedirs(self.vectorstore_path, exist_ok=True)
        
        # LLM for generation
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-2.5-flash",
            temperature=0.5  # Balance creativity and accuracy
        )
        
        # Library assistant prompt template
        self.prompt_template = """You are an intelligent library assistant helping students understand study materials. You have access to book excerpts and your own knowledge base.

Guidelines:
1. **Primary Source**: Start with information from the provided book content
2. **Elaborate & Expand**: Don't just repeat - explain concepts in detail with examples
3. **Fill Knowledge Gaps**: If the book mentions concepts without full explanations, use your knowledge to provide complete definitions
4. **Hybrid Approach**: Combine book content with general knowledge for comprehensive answers
5. **Transparency**: If you add information beyond the book, mention it (e.g., "The book mentions X. Additionally, X refers to...")
6. **Educational Tone**: Explain as if teaching a student who wants deep understanding

Book Content:
{context}

Student Question: {question}

Comprehensive Answer (combining book content and relevant knowledge):"""
    
    def clean_text(self, text: str) -> str:
        """Remove noise from PDF text (headers, footers, metadata)"""
        # Remove common header/footer patterns
        text = re.sub(r'(Chapter|Section)\s*\d+.*?\n', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Page\s*\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\d+\s*/\s*\d+', '', text)  # Page numbers like "5 / 111"
        
        # Remove metadata noise
        text = re.sub(r'©.*?\d{4}', '', text)  # Copyright
        text = re.sub(r'ISBN.*?\n', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\S+@\S+', '', text)  # Email addresses
        text = re.sub(r'http[s]?://\S+', '', text)  # URLs
        
        # Clean excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def is_similar(self, text1: str, text2: str, threshold: float = 0.85) -> bool:
        """Check if two texts are similar (for deduplication)"""
        return SequenceMatcher(None, text1, text2).ratio() > threshold
    
    def process_pdf(self, pdf_path: str, book_id: int) -> Dict:
        """
        Complete PDF processing pipeline:
        1. Load PDF
        2. Clean text (remove headers, footers, noise)
        3. Chunk text intelligently
        4. Deduplicate chunks (remove 85%+ similar)
        5. Generate embeddings
        6. Store in ChromaDB vector store
        
        Returns: Processing statistics
        """
        try:
            # Step 1: Load PDF
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            
            if not docs:
                return {
                    "success": False,
                    "error": "Failed to load PDF or PDF is empty"
                }
            
            # Step 2: Clean text
            for doc in docs:
                doc.page_content = self.clean_text(doc.page_content)
            
            # Step 3: Chunk text intelligently
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=600,  # Optimal for educational content
                chunk_overlap=150,  # Preserve context at boundaries
                separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ": ", " ", ""]
            )
            splits = text_splitter.split_documents(docs)
            
            # Step 4: Advanced deduplication
            unique_splits = []
            for split in splits:
                content = split.page_content.strip()
                
                # Skip chunks that are too short
                if len(content) < 100:
                    continue
                
                # Check against existing unique chunks
                is_duplicate = False
                for existing in unique_splits:
                    if self.is_similar(content.lower(), existing.page_content.lower()):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    # Add book_id to metadata for filtering
                    split.metadata['book_id'] = book_id
                    unique_splits.append(split)
            
            if not unique_splits:
                return {
                    "success": False,
                    "error": "No valid chunks after deduplication (PDF might be too short or corrupted)"
                }
            
            # Step 5 & 6: Generate embeddings and store in ChromaDB
            collection_name = f"book_{book_id}"
            
            # Create/update vector store for this book
            vectorstore = Chroma.from_documents(
                documents=unique_splits,
                embedding=self.embeddings,
                collection_name=collection_name,
                persist_directory=self.vectorstore_path
            )
            
            # Calculate deduplication percentage
            dedup_percentage = ((len(splits) - len(unique_splits)) / len(splits) * 100) if splits else 0
            
            return {
                "success": True,
                "total_pages": len(docs),
                "total_chunks": len(splits),
                "unique_chunks": len(unique_splits),
                "deduplication_percentage": round(dedup_percentage, 2),
                "collection_name": collection_name,
                "message": f"Successfully indexed {len(unique_splits)} unique chunks from {len(docs)} pages"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"PDF processing failed: {str(e)}"
            }
    
    def query_book(self, book_id: int, question: str, num_chunks: int = 5) -> Dict:
        """
        Query a specific book using RAG:
        1. Load vectorstore for book
        2. Retrieve relevant chunks using MMR (Maximal Marginal Relevance)
        3. Format context
        4. Generate comprehensive answer with LLM
        
        Args:
            book_id: ID of the book to query
            question: Student's question
            num_chunks: Number of chunks to retrieve (default 5)
        
        Returns: Answer with sources
        """
        try:
            collection_name = f"book_{book_id}"
            
            # Load existing vectorstore
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.vectorstore_path
            )
            
            # MMR retriever for diverse, relevant chunks
            # MMR = Maximal Marginal Relevance
            # - Balances relevance (similarity to query) with diversity (different from each other)
            # - Prevents retrieving 5 chunks that all say the same thing
            retriever = vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": num_chunks,  # Return this many chunks
                    "fetch_k": num_chunks * 3,  # Initially fetch 3x candidates
                    "lambda_mult": 0.7  # 70% relevance, 30% diversity
                }
            )
            
            # Format retrieved chunks
            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)
            
            # Build RAG chain
            prompt = ChatPromptTemplate.from_template(self.prompt_template)
            
            rag_chain = (
                {"context": retriever | format_docs, "question": RunnablePassthrough()}
                | prompt
                | self.llm
                | StrOutputParser()
            )
            
            # Generate answer
            answer = rag_chain.invoke(question)
            
            # Get source chunks for transparency
            retrieved_docs = retriever.invoke(question)
            sources = [
                {
                    "page": doc.metadata.get('page', 'N/A'),
                    "preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                }
                for doc in retrieved_docs
            ]
            
            return {
                "success": True,
                "question": question,
                "answer": answer,
                "sources": sources,
                "num_chunks_used": len(retrieved_docs)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Query failed: {str(e)}"
            }
    
    def delete_book_index(self, book_id: int) -> Dict:
        """Delete vector store for a book"""
        try:
            collection_name = f"book_{book_id}"
            
            # Delete ChromaDB collection
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.vectorstore_path
            )
            vectorstore.delete_collection()
            
            return {
                "success": True,
                "message": f"Deleted vector index for book {book_id}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete index: {str(e)}"
            }
    
    def check_index_status(self, book_id: int) -> Dict:
        """Check if a book is indexed in ChromaDB"""
        try:
            collection_name = f"book_{book_id}"
            
            # Try to load the collection
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.vectorstore_path
            )
            
            # Check if collection has documents
            # Note: Chroma returns the collection even if it's empty
            # We need to check if it actually has documents
            try:
                # Try to get count - if collection doesn't exist, this will fail
                collection = vectorstore._client.get_collection(collection_name)
                count = collection.count()
                
                return {
                    "indexed": count > 0,
                    "collection_name": collection_name,
                    "document_count": count,
                    "message": f"Collection has {count} documents" if count > 0 else "Collection is empty"
                }
            except:
                # Collection doesn't exist
                return {
                    "indexed": False,
                    "collection_name": collection_name,
                    "document_count": 0,
                    "message": "Collection not found"
                }
                
        except Exception as e:
            return {
                "indexed": False,
                "collection_name": f"book_{book_id}",
                "document_count": 0,
                "error": str(e),
                "message": "Failed to check index status"
            }


# Singleton instance
rag_service = RAGService()

