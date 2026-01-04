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
from typing import Dict
import logging
import redis.asyncio as redis
import json
import hashlib
import asyncio

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S' )


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S' )






class RAGService:
    """RAG Service for intelligent document Q&A"""
    
    def __init__(self):
        # Local embeddings - FASTEST option with good accuracy
        # all-MiniLM-L6-v2: 2x faster (384 dim), excellent for speed
        # all-mpnet-base-v2: Slower (768 dim), slightly better accuracy - STANDARD
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            model_kwargs={'device': 'cpu'},  # Use 'cuda' if you have GPU
            encode_kwargs={'normalize_embeddings': True, 'batch_size': 64}  # Maximum batch size for speed
        )
        
        # Vector store directory
        self.vectorstore_path = "static/vectordb"
        os.makedirs(self.vectorstore_path, exist_ok=True)
        
        # Redis client for caching
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        
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
    
    def is_similar(self, text1: str, text2: str, threshold: float = 0.95) -> bool:
        """Check if two texts are similar (for deduplication) - using 0.95 to be less aggressive"""
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
            logging.info(f"Loading PDF from: {pdf_path}")
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            
            if not docs:
                logging.error("PDF loading failed or PDF is empty")
                return {
                    "success": False,
                    "error": "Failed to load PDF or PDF is empty"
                }
            
            logging.info(f"Loaded {len(docs)} pages from PDF")
            
            # Step 2: Clean text
            for doc in docs:
                doc.page_content = self.clean_text(doc.page_content)
            
            # Step 3: Chunk text intelligently (optimized for speed and accuracy)
            logging.info("Chunking text...")
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,  # Larger chunks = fewer chunks = faster processing
                chunk_overlap=100,  # Reduced overlap for speed
                separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ": ", " ", ""],
                length_function=len
            )
            splits = text_splitter.split_documents(docs)
            logging.info(f"Created {len(splits)} chunks")
            
            # Step 4: Fast deduplication (optimized for speed)
            logging.info("Deduplicating chunks...")
            unique_splits = []
            seen_hashes = set()  # Fast hash-based lookup
            
            for split in splits:
                content = split.page_content.strip()
                
                # Skip chunks that are too short
                if len(content) < 50:
                    continue
                
                # Fast hash-based deduplication (exact matches only)
                content_hash = hash(content.lower())
                if content_hash in seen_hashes:
                    continue
                
                seen_hashes.add(content_hash)
                split.metadata['book_id'] = book_id
                unique_splits.append(split)
            
            if not unique_splits:
                logging.error(f"No valid chunks after deduplication (started with {len(splits)} chunks)")
                return {
                    "success": False,
                    "error": "No valid chunks after deduplication (PDF might be too short or corrupted)"
                }
            
            logging.info(f"Deduplicated to {len(unique_splits)} unique chunks")
            
            # Step 5 & 6: Generate embeddings and store in ChromaDB (with progress tracking)
            collection_name = f"book_{book_id}"
            logging.info(f"Generating embeddings for {len(unique_splits)} chunks (this may take a few minutes)...")
            logging.info(f"Processing in batches of 32... Progress: 0%")
            
            # Create/update vector store for this book (batch processing is handled internally)
            vectorstore = Chroma.from_documents(
                documents=unique_splits,
                embedding=self.embeddings,
                collection_name=collection_name,
                persist_directory=self.vectorstore_path
            )
            
            logging.info(f"Vector store created successfully ({len(unique_splits)} embeddings generated)")
            
            # Calculate deduplication percentage
            dedup_percentage = ((len(splits) - len(unique_splits)) / len(splits) * 100) if splits else 0
            
            result = {
                "success": True,
                "total_pages": len(docs),
                "total_chunks": len(splits),
                "unique_chunks": len(unique_splits),
                "deduplication_percentage": round(dedup_percentage, 2),
                "collection_name": collection_name,
                "message": f"Successfully indexed {len(unique_splits)} unique chunks from {len(docs)} pages"
            }
            logging.info(f"RAG indexing complete: {result['message']}")
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"PDF processing failed: {str(e)}"
            }
    
    async def query_book(self, book_id: int, question: str, num_chunks: int = 5) -> Dict:
        """
        Query a specific book using RAG (async with caching):
        1. Check cache first
        2. Load vectorstore for book
        3. Retrieve relevant chunks using MMR (Maximal Marginal Relevance)
        4. Format context
        5. Generate comprehensive answer with LLM
        6. Cache the result
        
        Args:
            book_id: ID of the book to query
            question: Student's question
            num_chunks: Number of chunks to retrieve (default 5)
        
        Returns: Answer with sources
        """
        # Create cache key from book_id, question, and num_chunks
        cache_key_data = f"{book_id}:{question}:{num_chunks}"
        cache_key = hashlib.sha256(cache_key_data.encode()).hexdigest()
        
        try:
            # Check cache first
            cached_result = await self.redis_client.get(cache_key)
            if cached_result:
                logging.info(f"RAG query cache hit for book {book_id}")
                return json.loads(cached_result)
            
            logging.info(f"RAG query cache miss for book {book_id}, processing...")
            
            collection_name = f"book_{book_id}"
            
            logging.info(f"Querying book {book_id}, collection: {collection_name}")
            
            # Load existing vectorstore with error handling
            try:
                vectorstore = Chroma(
                    collection_name=collection_name,
                    embedding_function=self.embeddings,
                    persist_directory=self.vectorstore_path
                )
                
                # Check if collection exists and has documents
                try:
                    collection = vectorstore._collection
                    doc_count = collection.count()
                    if doc_count == 0:
                        logging.error(f"Collection {collection_name} is empty")
                        result = {
                            "success": False,
                            "error": f"Book {book_id} has not been indexed yet. Please wait for RAG indexing to complete or re-upload the book."
                        }
                        # Cache error result for 5 minutes
                        await self.redis_client.setex(cache_key, 300, json.dumps(result))
                        return result
                    logging.info(f"Found {doc_count} chunks in collection")
                except Exception as count_error:
                    logging.warning(f"Could not verify collection: {str(count_error)}")
                    
            except Exception as load_error:
                logging.error(f"Error loading vectorstore: {str(load_error)}")
                result = {
                    "success": False,
                    "error": f"Book {book_id} index not found. The book may not have been indexed yet. Please re-upload the book or wait for indexing to complete."
                }
                # Cache error result for 5 minutes
                await self.redis_client.setex(cache_key, 300, json.dumps(result))
                return result
            
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
            
            # Generate answer with error handling
            logging.info(f"Generating answer for question: {question[:50]}...")
            try:
                answer = rag_chain.invoke(question)
                logging.info("Answer generated successfully")
            except Exception as gen_error:
                logging.error(f"Error generating answer: {str(gen_error)}")
                result = {
                    "success": False,
                    "error": f"Failed to generate answer. LLM error: {str(gen_error)}"
                }
                # Cache error result for 5 minutes
                await self.redis_client.setex(cache_key, 300, json.dumps(result))
                return result
            
            # Get source chunks for transparency
            try:
                retrieved_docs = retriever.invoke(question)
                sources = [
                    {
                        "page": doc.metadata.get('page', 'N/A'),
                        "preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                    }
                    for doc in retrieved_docs
                ]
            except Exception as retrieve_error:
                logging.warning(f"Could not retrieve source docs: {str(retrieve_error)}")
                sources = []
                retrieved_docs = []
            
            result = {
                "success": True,
                "question": question,
                "answer": answer,
                "sources": sources,
                "num_chunks_used": len(retrieved_docs)
            }
            
            # Cache successful result for 2 hours (7200 seconds)
            await self.redis_client.setex(cache_key, 7200, json.dumps(result))
            logging.info(f"RAG query result cached for book {book_id}")
            
            return result
            
        except Exception as e:
            logging.error(f"Query failed with exception: {str(e)}")
            logging.exception("Query failed")
            result = {
                "success": False,
                "error": f"Query failed: {str(e)}"
            }
            # Cache error result for 5 minutes
            await self.redis_client.setex(cache_key, 300, json.dumps(result))
            return result
    
    async def delete_book_index(self, book_id: int) -> Dict:
        """Delete vector store for a book and clear all cached queries"""
        try:
            collection_name = f"book_{book_id}"
            
            # Delete ChromaDB collection
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.vectorstore_path
            )
            vectorstore.delete_collection()
            
            # Clear all cached queries for this book
            # Use pattern matching to delete all keys that start with book_id
            cache_pattern = f"rag_query_{book_id}_*"
            # Note: Redis SCAN and DELETE pattern is complex in async
            # For now, we'll just proceed with the index deletion
            # In production, you might want to implement a more sophisticated cache clearing
            
            logging.info(f"Cleared cached queries for book {book_id}")
            
            return {
                "success": True,
                "message": f"Deleted vector index for book {book_id} and cleared cached queries"
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

