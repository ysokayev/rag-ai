import os
import glob
import pickle
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI
import time
# Try importing pypdf, handle if missing
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# Configuration
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.tmp')
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

class RAGEngine:
    def __init__(self, cache_file_name: str = "rag_cache.pkl", rebuild_index: bool = False):
        self.load_environment()
        self.client = OpenAI()
        self.cache_path = os.path.join(CACHE_DIR, cache_file_name)
        self.ensure_directories()
        
        if not rebuild_index and os.path.exists(self.cache_path):
            self.load_index()
        else:
            self.index = [] # Start fresh if rebuilding or no cache

    def load_environment(self):
        """Load environment variables."""
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        load_dotenv(dotenv_path)
        if not os.getenv("OPENAI_API_KEY"):
            print("Warning: OPENAI_API_KEY not found in .env file")

    def ensure_directories(self):
        """Ensure necessary directories exist."""
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

    def load_index(self):
        """Load index from cache and build matrix."""
        print(f"Loading index from {self.cache_path}...")
        try:
            with open(self.cache_path, 'rb') as f:
                self.index = pickle.load(f)
            print(f"Loaded {len(self.index)} chunks from cache.")
            self._build_matrix()
        except Exception as e:
            print(f"Error loading cache: {e}. Starting with empty index.")
            self.index = []
            self.embeddings_matrix = None

    def _build_matrix(self):
        """Rebuild numpy matrix from index."""
        if not self.index:
            self.embeddings_matrix = None
            return
            
        # Extract embeddings
        try:
            # Filter items that might be malformed
            valid_items = [item for item in self.index if "embedding" in item and len(item["embedding"]) == 1536]
            if not valid_items:
                 self.embeddings_matrix = None
                 return
                 
            self.embeddings_matrix = np.array([item["embedding"] for item in valid_items], dtype='float32')
            # Normalize matrix for cosine similarity (if vectors aren't already normalized)
            # embeddings from openai are usually normalized, but let's be safe for dot product = cosine similarity
            # Actually, standard is dot product of normalized vectors. 
            # Vector normalization:
            norms = np.linalg.norm(self.embeddings_matrix, axis=1, keepdims=True)
            # Avoid divide by zero
            norms[norms == 0] = 1
            self.embeddings_matrix = self.embeddings_matrix / norms
        except Exception as e:
            print(f"Error building matrix: {e}")
            self.embeddings_matrix = None

    def save_index(self):
        """Save index to cache."""
        # We only save the list, matrix is rebuilt on load/update
        print(f"Saving index to {self.cache_path}...")
        with open(self.cache_path, 'wb') as f:
            pickle.dump(self.index, f)

    def ingest_files(self, file_paths: List[str]):
        """Ingest a list of specific file paths."""
        # 1. Identify new files
        existing_paths = set(item['path'] for item in self.index if 'path' in item)
        new_paths = [p for p in file_paths if p not in existing_paths]
        
        if not new_paths:
            print("All files already indexed.")
            return

        print(f"Found {len(new_paths)} new files to ingest.")
        
        # 2. Process in chunks of files to allow incremental saving
        file_batch_size = 10
        for i in range(0, len(new_paths), file_batch_size):
            batch_paths = new_paths[i:i + file_batch_size]
            docs_batch = []
            
            for path in batch_paths:
                if not os.path.exists(path):
                    continue
                content = self._read_file(path)
                if content:
                    docs_batch.append({"source": os.path.basename(path), "text": content, "path": path})
            
            self._process_and_index(docs_batch)
            print(f"Saved progress after {i + len(batch_paths)}/{len(new_paths)} files.")

    def ingest_directories(self, directories: List[str], recursive: bool = True):
        """Ingest all supported files from directories."""
        all_files = []
        extensions = ['*.txt', '*.csv', '*.pdf', '*.md']
        
        for dir_path in directories:
            if not os.path.exists(dir_path):
                continue
            for ext in extensions:
                pattern = os.path.join(dir_path, '**', ext) if recursive else os.path.join(dir_path, ext)
                files = glob.glob(pattern, recursive=recursive)
                all_files.extend([f for f in files if not os.path.basename(f).startswith('.')])
        
        # Remove duplicates
        all_files = list(set(all_files))
        self.ingest_files(all_files)

    def _read_file(self, file_path: str) -> Optional[str]:
        # Silence the read print to reduce noise
        # print(f"Reading {os.path.basename(file_path)}...", end='\r')
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == '.txt' or ext == '.md':
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()
            elif ext == '.csv':
                try:
                    df = pd.read_csv(file_path)
                    return df.to_string(index=False)
                except:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        return f.read()
            elif ext == '.pdf':
                if PdfReader:
                    reader = PdfReader(file_path)
                    text = ""
                    for page in reader.pages:
                         extracted = page.extract_text()
                         if extracted:
                             text += extracted + "\n"
                    return text
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None

    def chunk_text(self, text: str, chunk_size: int = 1500, overlap: int = 300) -> List[str]:
        chunks = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += (chunk_size - overlap)
        return chunks

    def _process_and_index(self, docs: List[Dict]):
        if not docs:
            return

        all_chunk_texts = []
        indexed_chunks = [] 

        for doc in docs:
            chunks = self.chunk_text(doc["text"])
            for c in chunks:
                all_chunk_texts.append(c)
                indexed_chunks.append({"text": c, "source": doc["source"], "path": doc["path"]})
        
        if not all_chunk_texts:
            return

        print(f"Embedding {len(all_chunk_texts)} chunks for {len(docs)} files...")
        embeddings = self.get_embeddings(all_chunk_texts)
        
        for i, emb in enumerate(embeddings):
            indexed_chunks[i]["embedding"] = emb
        
        self.index.extend(indexed_chunks)
        self.save_index()
        # Rebuild matrix to include new chunks
        self._build_matrix()

    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        if not self.index or self.embeddings_matrix is None:
            return []
            
        try:
            query_emb = self.client.embeddings.create(input=[query], model=EMBEDDING_MODEL).data[0].embedding
        except Exception as e:
            print(f"Error embedding query: {e}")
            return []
            
        query_vec = np.array(query_emb, dtype='float32')
        # Normalize query vector
        norm = np.linalg.norm(query_vec)
        if norm > 0:
            query_vec = query_vec / norm
        
        # Vectorized Cosine Similarity: Matrix (N, D) dot Vector (D,) -> Scores (N,)
        scores = np.dot(self.embeddings_matrix, query_vec)
        
        # Get top k indices
        # argsort sorts ascending, so take last k and reverse
        top_k_indices = np.argsort(scores)[-k:][::-1]
        
        return [self.index[i] for i in top_k_indices]

    def query(self, query: str, k: int = 5) -> str:
        top_chunks = self.retrieve(query, k=k)
        if not top_chunks:
            return "No relevant information found in the documents."
            
        context_str = ""
        for chunk in top_chunks:
            context_str += f"\n--- Source: {chunk['source']} ---\n{chunk['text']}\n"
            
        prompt = (
            "You are an expert architect and engineering assistant.\n"
            "Use the provided Context to answer the user's specific requirement question.\n"
            "Instructions:\n"
            "1. Be precise. Extract numbers, boolean values (Yes/No), or lists as requested.\n"
            "2. If there are conflicting values, note them, but per user instruction: 'always default to the largest number of receptacles wherever there is conflict'.\n"
            "3. If information is missing, state 'Not Found'.\n"
            f"\nContext:\n{context_str}\n\nQuestion: {query}"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error querying LLM: {e}"
