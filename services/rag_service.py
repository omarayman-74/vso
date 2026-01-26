"""RAG service for document loading, chunking, and vector search."""
import os
import re
import sys
import shutil
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
from langchain_core.documents import Document
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_community.vectorstores import Chroma
# from langchain_community.document_loaders import PyPDFLoader

from config import settings

def safe_print(message):
    """
    Safely print messages to console, handling Unicode encoding errors on Windows.
    Falls back to ASCII representation if Unicode fails.
    """
    try:
        print(message)
    except UnicodeEncodeError:
        # Try encoding with errors='replace' to replace problematic characters
        try:
            safe_msg = message.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
            print(safe_msg)
        except:
            # Last resort: ASCII representation
            print(message.encode('ascii', errors='replace').decode('ascii'))


class RAGService:
    """Service for RAG operations including document processing and search."""
    
    def __init__(self):
        self.embeddings = None
        self.vectordb = None
        self.translation_cache = {}  # Cache for translated queries
        self.preprocessing_cache = {}  # Cache for preprocessed queries
        # Lazy initialization
    
    def _initialize(self):
        """Initialize embeddings and vector store if not already loaded."""
        if self.embeddings and self.vectordb:
            return
            
        print("Initializing RAG components...")
        from langchain_community.embeddings import HuggingFaceEmbeddings
        # The Chroma import is moved to _load_vectordb where it's first used
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            encode_kwargs={"normalize_embeddings": True}
        )
        self._load_vectordb()

    def _load_vectordb(self):
        """Load existing vector database or create a new one."""
        # The import is moved inside the try block for true lazy loading
        
        if os.path.exists(settings.rag_db_path):
            try:
                from langchain_community.vectorstores import Chroma
                self.vectordb = Chroma(
                    persist_directory=settings.rag_db_path,
                    embedding_function=self.embeddings
                )
                print(f"SUCCESS: Loaded existing RAG database from {settings.rag_db_path}")
            except Exception as e:
                print(f"WARNING: Error loading RAG database: {e}")
                print("Will rebuild database if data files are available.")
                self._rebuild_database()
        else:
            print(f"WARNING: RAG database not found at {settings.rag_db_path}")
            self._rebuild_database()
    
    def _rebuild_database(self):
        """Rebuild vector database from data files."""
        data_dir = "./data"
        if not os.path.exists(data_dir):
            print(f"WARNING: Data directory not found: {data_dir}")
            return
        
        # Find PDF and TXT files
        files = []
        for file in os.listdir(data_dir):
            if file.endswith(('.pdf', '.txt')):
                files.append(os.path.join(data_dir, file))
        
        if not files:
            print("WARNING: No PDF or TXT files found in data directory")
            return
        
        print(f"Rebuilding RAG database from {len(files)} files...")
        self.prepare_rag_from_files(files)
    
    @staticmethod
    def clean_pdf_text(text: str) -> str:
        """Remove noise from PDF text for better embedding quality."""
        text = re.sub(r"\s{3,}", " ", text)
        text = re.sub(r"[\n\r]{2,}", "\n\n", text)
        text = re.sub(r"-\s*\n", "", text)
        text = re.sub(r"•", "-", text)
        return text.strip()
    
    @staticmethod
    def load_txt_file(txt_path: str) -> str:
        """Load text file content."""
        with open(txt_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def enhanced_chunk_policy_text(self, text: str) -> List[Document]:
        """
        Advanced chunking with section detection and metadata.
        """
        text = self.clean_pdf_text(text)
        
        # Section pattern detection
        section_pattern = r"(\n\d+\.\s+[A-Za-z0-9 &]+|\n[A-Z][A-Z\s]{3,}:)"
        parts = re.split(section_pattern, text)
        
        section_docs = []
        current_section = "Introduction"
        
        for i in range(1, len(parts), 2):
            title = parts[i].strip().replace("\n", "")
            content = parts[i + 1].strip() if i + 1 < len(parts) else ""
            
            if not content or len(content.split()) < 10:
                continue
            
            from langchain_core.documents import Document
            section_docs.append(
                Document(
                    page_content=f"Section: {title}\n\n{content}",
                    metadata={
                        "section": title,
                        "original_length": len(content),
                        "word_count": len(content.split())
                    }
                )
            )
        

        
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=900,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        chunks = []
        for doc in section_docs:
            small_chunks = splitter.split_documents([doc])
            
            for i, chunk in enumerate(small_chunks):
                chunk.metadata.update({
                    "chunk_id": f"{chunk.metadata['section']}_{i}",
                    "index": i,
                    "total_in_section": len(small_chunks)
                })
                chunks.append(chunk)
        
        print(f"SUCCESS: Created {len(chunks)} chunks from {len(section_docs)} sections")
        return chunks
    
    def embed_and_store(self, chunks: List[Document]):
        """Create and persist vector store from chunks."""
        if os.path.exists(settings.rag_db_path):
            shutil.rmtree(settings.rag_db_path)
        
        from langchain_community.vectorstores import Chroma
        self.vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=settings.rag_db_path,
            collection_metadata={"hnsw:space": "cosine"}
        )
        
        self.vectordb.persist()
        print(f"SUCCESS: RAG database created at {settings.rag_db_path}")
    
    def prepare_rag_from_files(self, file_paths: List[str]):
        """Prepare RAG database from multiple files."""
        # Ensure initialized before rebuilding
        if not self.embeddings:
             print("Initializing embeddings for rebuild...")
             from langchain_community.embeddings import HuggingFaceEmbeddings
             self.embeddings = HuggingFaceEmbeddings(
                model_name=settings.embedding_model,
                encode_kwargs={"normalize_embeddings": True}
            )

        all_chunks = []
        
        for file_path in file_paths:
            print(f"Loading file: {file_path}")
            
            if file_path.lower().endswith(".pdf"):
                from langchain_community.document_loaders import PyPDFLoader
                docs = PyPDFLoader(file_path).load()
                full_text = "\n".join([d.page_content for d in docs])
            elif file_path.lower().endswith(".txt"):
                full_text = self.load_txt_file(file_path)
            else:
                print(f"WARNING: Unsupported file type: {file_path}")
                continue
            
            print("Cleaning + Chunking...")
            chunks = self.enhanced_chunk_policy_text(full_text)
            
            for c in chunks:
                c.metadata["source_file"] = os.path.basename(file_path)
            
            all_chunks.extend(chunks)
        
        print(f"Total chunks from all files: {len(all_chunks)}")
        
        print("Embedding & storing in Chroma DB...")
        self.embed_and_store(all_chunks)
        
        print("RAG database ready!")
    
    def _translate_with_cache(self, query: str, src_lang: str, tgt_lang: str) -> str:
        """Translate query with caching to avoid redundant translations."""
        cache_key = f"{src_lang}:{tgt_lang}:{query}"
        
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]
        
        # Import here to avoid circular dependency
        from services.language_service import translate_text_logic_func
        
        translated = translate_text_logic_func(query, src_lang, tgt_lang)
        self.translation_cache[cache_key] = translated
        
        # Limit cache size to prevent memory bloat
        if len(self.translation_cache) > 1000:
            # Remove oldest 200 entries
            keys_to_remove = list(self.translation_cache.keys())[:200]
            for key in keys_to_remove:
                del self.translation_cache[key]
        
        return translated
    
    def _preprocess_query(self, query: str, language: Optional[str] = None) -> dict:
        """
        Preprocess and normalize query to improve RAG matching.
        Fixes grammar, spelling, transliterations, and rephrases for better semantic search.
        
        Args:
            query: Original user query
            language: Detected language ('ar', 'en', 'franco', or None)
            
        Returns:
            dict with 'preprocessed', 'original', 'changes_made'
        """
        # Check cache first
        cache_key = f"{language}:{query}"
        if cache_key in self.preprocessing_cache:
            return self.preprocessing_cache[cache_key]
        
        # If query is very short or simple, skip preprocessing
        from config import settings
        min_words = settings.preprocessing_min_words
        if len(query.strip().split()) < min_words:
            result = {
                'preprocessed': query,
                'original': query,
                'changes_made': [],
                'skipped': True
            }
            return result
        
        try:
            # Import LLM
            from services.agent_service import _get_llm
            
            # Language-specific preprocessing instructions
            lang_instructions = ""
            if language in ['ar', 'arabic']:
                lang_instructions = """
**Arabic-specific corrections:**
- Convert English transliterations to proper Arabic:
  - "شيرهولدرز" → "المساهمين" (shareholders)
  - "ميتينج" → "اجتماع" (meeting)
  - "بروبرتي" → "عقار" (property)
  - "أبارتمنت" → "شقة" (apartment)
- Use proper Arabic vocabulary for real estate terms
"""
            elif language in ['franco', 'franco_arabic', 'franco-arabic']:
                lang_instructions = """
**Franco-Arabic specific:**
- Keep Franco-Arabic format (Latin letters + numbers)
- Fix obvious typos but maintain Franco style
- Don't translate to pure English or Arabic
"""
            else:
                lang_instructions = """
**English-specific corrections:**
- Fix grammar errors
- Correct spelling mistakes
- Use real estate terminology
"""
            
            prompt = f"""You are a strict query normalizer for a real estate chatbot.
Your goal is to ensure consistency by fixing ALL spelling and grammar mistakes.

**Original Query:** "{query}"
**Detected Language:** {language or 'unknown'}

**Instructions:**
1. **FIX SPELLING/GRAMMAR**: Correct any typos or grammatical errors.
2. **NORMALIZE TERMS**:
   - If user says "sharholders" -> convert to "shareholders"
   - If user says "poclicy" -> convert to "policy"
   - If user says "paymnet" -> convert to "payment"
3. **DO NOT TRANSLATE**: Keep the language exactly as is (English stays English, Arabic stays Arabic).
4. **DO NOT CHANGE MEANING**: Only fix the form, not the intent.

{lang_instructions}

**Return ONLY valid JSON:**
{{
  "preprocessed_query": "corrected query here",
  "changes_made": ["fixed spelling 'sharholder' -> 'shareholder'", "fixed grammar"]
}}
"""
            
            # Call LLM for preprocessing
            response = _get_llm().invoke(prompt)
            result_text = response.content.strip()
            
            # Clean JSON formatting
            result_text = result_text.replace('```json', '').replace('```', '').strip()
            
            # Parse JSON
            import json
            parsed = json.loads(result_text)
            
            result = {
                'preprocessed': parsed.get('preprocessed_query', query),
                'original': query,
                'changes_made': parsed.get('changes_made', []),
                'skipped': False
            }
            
            # Cache the result
            self.preprocessing_cache[cache_key] = result
            
            # Limit cache size
            if len(self.preprocessing_cache) > 500:
                # Remove oldest 100 entries
                keys_to_remove = list(self.preprocessing_cache.keys())[:100]
                for key in keys_to_remove:
                    del self.preprocessing_cache[key]
            
            return result
            
        except Exception as e:
            # If preprocessing fails, use original query
            print(f"[RAG] Preprocessing failed: {e}")
            return {
                'preprocessed': query,
                'original': query,
                'changes_made': [],
                'error': str(e)
            }
    
    def _deduplicate_documents(self, docs: List[Document]) -> List[Document]:
        """Remove duplicate documents based on content similarity."""
        if not docs:
            return []
        
        unique_docs = []
        seen_contents = set()
        
        for doc in docs:
            # Create a normalized fingerprint of the content
            content_fingerprint = doc.page_content.strip().lower()[:200]  # First 200 chars
            
            if content_fingerprint not in seen_contents:
                seen_contents.add(content_fingerprint)
                unique_docs.append(doc)
        
        return unique_docs
    
    def search(self, query: str, k: int = 10, language: Optional[str] = None) -> str:
        """
        Perform similarity search on vector database with cross-lingual support.
        
        Args:
            query: The search query
            k: Number of results to return
            language: Detected language ('ar', 'en', 'franco', or None)
        
        Returns:
            Formatted search results
        """
        self._initialize()
        
        if not self.vectordb:
            return "RAG Error: Vector database not initialized"
        
        try:
            debug_enabled = settings.enable_rag_debug
            # PREPROCESSING LAYER - Automatically clean and improve query
            preprocessing_result = self._preprocess_query(query, language)
            preprocessed_query = preprocessing_result['preprocessed']
            
            # Debug logging (Windows console safe for Arabic/Unicode)
            if debug_enabled:
                print(f"\n{'='*80}")
            
            # Safe print for Arabic/Unicode queries
            if debug_enabled:
                try:
                    print(f"[RAG DEBUG] Original query: {query[:80]}..." if len(query) > 80 else f"[RAG DEBUG] Original query: {query}")
                except UnicodeEncodeError:
                    print(f"[RAG DEBUG] Original query: [Unicode query - {len(query)} chars]")
            
            # Show preprocessing if changes were made
            if debug_enabled:
                if preprocessed_query != query:
                    try:
                        safe_print(f"[RAG DEBUG] Preprocessed to: {preprocessed_query[:80]}..." if len(preprocessed_query) > 80 else f"[RAG DEBUG] Preprocessed to: {preprocessed_query}")
                    except UnicodeEncodeError:
                        safe_print(f"[RAG DEBUG] Preprocessed to: [Unicode query - {len(preprocessed_query)} chars]")
                    safe_print(f"[RAG DEBUG] Changes: {', '.join(preprocessing_result.get('changes_made', []))}")
                else:
                    safe_print(f"[RAG DEBUG] No preprocessing needed")
                
                print(f"[RAG DEBUG] Query length: {len(preprocessed_query)} chars")
                print(f"[RAG DEBUG] Language: {language}")
                print(f"[RAG DEBUG] Embedding model: {settings.embedding_model}")
            
            # Use MMR (Maximal Marginal Relevance) for diversified retrieval
            # This helps ensure we get chunks from different sections, not just most similar
            # Fetch=2*k candidates, return k diverse ones
            try:
                docs = self.vectordb.max_marginal_relevance_search(
                    preprocessed_query, 
                    k=k,
                    fetch_k=min(k * 2, 50),  # Fetch more candidates for diversity
                    lambda_mult=0.3  # Favor diversity (0.3) over pure relevance to reduce language bias
                )
                # Convert to (doc, score) tuples for consistency with existing code
                # MMR doesn't return scores, so we'll use placeholder scores
                docs = [(doc, 0.0) for doc in docs]
            except Exception as mmr_error:
                if debug_enabled:
                    print(f"[RAG DEBUG] MMR failed ({mmr_error}), falling back to similarity search")
                # Fallback to regular similarity search if MMR not supported
                docs = self.vectordb.similarity_search_with_score(preprocessed_query, k=k)
            
            if debug_enabled:
                print(f"[RAG DEBUG] Retrieved {len(docs)} documents")
            
            # Show top 3 results with scores for debugging (UTF-8 safe)
            if debug_enabled:
                for i, (doc, score) in enumerate(docs[:3]):
                    preview = doc.page_content[:100].replace('\n', ' ')
                    print(f"[RAG DEBUG] Doc {i+1} - Score: {score:.4f}")
                    print(f"[RAG DEBUG]   Source: {doc.metadata.get('source_file', 'unknown')}")
                    print(f"[RAG DEBUG]   Preview length: {len(doc.page_content)} chars")
            
            # Format results
            final_docs = [doc for doc, score in docs]
            final_text = "\n\n".join([f"Chunk {i+1}:\n{d.page_content}" for i, d in enumerate(final_docs)])
            
            if debug_enabled:
                print(f"[RAG DEBUG] Total text returned: {len(final_text)} chars")
                print(f"{'='*80}\n")
            
            return final_text
            
        except Exception as e:
            if settings.enable_rag_debug:
                print(f"[RAG DEBUG] ERROR: {str(e)}")
                import traceback
                traceback.print_exc()
            return f"RAG Error: {str(e)}"


# Global RAG service instance
rag_service = RAGService()
