import os
import glob
import chromadb
import uuid
import time
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken

import argparse

# Configuration
# Default paths
# Default paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CHROMA_DIR = os.path.join(BASE_DIR, '.gemini', 'chroma_db')
EMBEDDING_MODEL = "text-embedding-3-large"

DOMAIN_MAP = {
    "healthcare": {"folder": "Code Books and Healthcare", "collection": "rag_healthcare"},
    "code": {"folder": "Code Books Only", "collection": "rag_code_only"},
    "military": {"folder": "Code Books and Military", "collection": "rag_military"},
}

# Chunking Configuration
PARENT_CHUNK_SIZE = 2000  # Tokens
CHILD_CHUNK_SIZE = 400    # Tokens
CHILD_OVERLAP = 100       # Tokens

def load_environment():
    """Load environment variables."""
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    load_dotenv(dotenv_path)
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found in .env file")

class ParentChildSplitter:
    def __init__(self, model_name="gpt-4"):
        self.encoder = tiktoken.encoding_for_model(model_name)

    def count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))

    def split_text(self, text: str, chunk_size: int, overlap: int = 0) -> List[str]:
        """Split text into chunks based on token count."""
        tokens = self.encoder.encode(text)
        chunks = []
        start = 0
        total_tokens = len(tokens)
        
        while start < total_tokens:
            end = min(start + chunk_size, total_tokens)
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoder.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            if end == total_tokens:
                break
                
            start += (chunk_size - overlap)
            
        return chunks

    def extract_metadata(self, text: str, source: str) -> Dict:
        """
        Extracts metadata using simple heuristics or regex.
        In a production system, this would be more robust.
        """
        meta = {
            "source_id": source.replace(" ", "_").replace(".", "_"), # Simple ID
            "source_title": source,
            "section_path": "Unknown", # Placeholder
            "rev": "Latest", # Placeholder
            "chunk_role": "normative", # Default
            "contains_formula": False
        }
        
        # Heuristic for calculation/formula
        calc_keywords = ["calculate", "load calculation", "demand factor", "VA per", "watts per", "table"]
        if any(k in text.lower() for k in calc_keywords):
            meta["contains_formula"] = True
            
        # Heuristic for Table
        if "Table" in text and ("|" in text or "\t" in text):
            meta["chunk_role"] = "table"
            
        return meta

    def create_parent_child_chunks(self, text: str, source: str, domain: str) -> List[Dict]:
        """
        Splits text into Parents, then splits Parents into Children.
        Returns a list of Child chunks with Parent metadata.
        """
        chunks_data = []
        
        # 1. Create Parent Chunks
        parent_chunks = self.split_text(text, PARENT_CHUNK_SIZE, overlap=100)
        
        print(f"  - Generated {len(parent_chunks)} Parent chunks.")
        
        for p_idx, parent_text in enumerate(parent_chunks):
            parent_id = f"{source}_p{p_idx}"
            
            # Simple metadata extraction for parent
            parent_meta = self.extract_metadata(parent_text, source)
            
            # 2. Create Child Chunks from this Parent
            child_chunks = self.split_text(parent_text, CHILD_CHUNK_SIZE, overlap=CHILD_OVERLAP)
            
            for c_idx, child_text in enumerate(child_chunks):
                chunk_id = f"{parent_id}_c{c_idx}"
                
                # Child inherits parent metadata but can refine specific formula detection
                child_meta = self.extract_metadata(child_text, source)
                
                # Merge metadata
                full_meta = {
                    "source": source,
                    "parent_id": parent_id,
                    "parent_text": parent_text,
                    "child_index": c_idx,
                    "parent_index": p_idx,
                    "source_title": parent_meta["source_title"],
                    "domain": domain,
                    "section_path": parent_meta["section_path"],
                    "chunk_role": child_meta["chunk_role"],
                    "contains_formula": child_meta["contains_formula"],
                    "rev": parent_meta["rev"]
                }
                
                chunks_data.append({
                    "id": chunk_id,
                    "text": child_text,
                    "metadata": full_meta
                })
                
        return chunks_data

def get_embeddings_batched(client: OpenAI, texts: List[str], batch_size: int = 50) -> List[List[float]]:
    """Generate embeddings with batching and retry logic."""
    all_embeddings = []
    
    total = len(texts)
    print(f"  - Generating embeddings for {total} chunks...")
    
    for i in range(0, total, batch_size):
        batch = texts[i:i + batch_size]
        attempts = 0
        while attempts < 3:
            try:
                response = client.embeddings.create(input=batch, model=EMBEDDING_MODEL)
                embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(embeddings)
                print(f"    - Processed batch {i}/{total}", end='\r')
                break
            except Exception as e:
                print(f"    - Error batch {i}: {e}. Retrying in 5s...")
                time.sleep(5)
                attempts += 1
        else:
             print(f"    - Failed batch {i} after retries.")
             # Fill with empty or raise error? For now, raise to stop inconsistent state
             raise Exception("Embedding generation failed.")
             
    print(f"    - Embeddings complete.             ")
    return all_embeddings

def main():
    parser = argparse.ArgumentParser(description="Ingest books into ChromaDB.")
    parser.add_argument("--domain", choices=DOMAIN_MAP.keys(), required=True, help="Domain to ingest (healthcare, code, military)")
    parser.add_argument("--reset", action="store_true", help="Delete existing collection and re-ingest")
    args = parser.parse_args()

    domain_config = DOMAIN_MAP[args.domain]
    folder_name = domain_config["folder"]
    collection_name = domain_config["collection"]
    
    books_dir = os.path.join(BASE_DIR, folder_name)

    load_environment()
    
    # 1. Initialize Clients
    client = OpenAI()
    splitter = ParentChildSplitter()
    
    print(f"Initializing ChromaDB at {CHROMA_DIR}...")
    if not os.path.exists(CHROMA_DIR):
        os.makedirs(CHROMA_DIR)
        
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    # Check if collection exists options
    if args.reset:
        try:
            print(f"[{args.domain.upper()}] Resetting collection '{collection_name}'...")
            chroma_client.delete_collection(collection_name)
        except Exception as e:
            print(f"Collection delete skipped: {e}")
            
    try:
        collection = chroma_client.get_collection(name=collection_name)
        print(f"[{args.domain.upper()}] Found existing collection '{collection_name}' with {collection.count()} items.")
    except:
        print(f"[{args.domain.upper()}] Creating new collection '{collection_name}'...")
        collection = chroma_client.create_collection(name=collection_name)

    # 2. Read Files
    if not os.path.exists(books_dir):
        print(f"Error: Directory not found: {books_dir}")
        return

    txt_files = glob.glob(os.path.join(books_dir, "*.txt"))
    if not txt_files:
        print(f"No .txt files found in {folder_name}/.")
        return

    # 3. Process Each File
    for file_path in txt_files:
        file_name = os.path.basename(file_path)
        
        # Check if file already ingested (naive check by source metadata)
        # Ideally we query specific metadata, but Chroma simple query is by embeddings or get by ids.
        # We can do a get with where filter.
        existing_count = collection.count()
        if existing_count > 0:
            results = collection.get(where={"source": file_name}, limit=1)
            if results["ids"]:
                print(f"Skipping {file_name} (already indexed).")
                continue
        
        print(f"Processing {file_name}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 4. Generate Chunks
            chunks = splitter.create_parent_child_chunks(content, file_name, args.domain)
            if not chunks:
                print(f"  - No chunks generated for {file_name}.")
                continue
                
            # 5. Generate Embeddings & Add to DB
            texts = [c["text"] for c in chunks]
            ids = [c["id"] for c in chunks]
            metadatas = [c["metadata"] for c in chunks]
            
            embeddings = get_embeddings_batched(client, texts)
            
            # Add to Chroma in batches to be safe? Chroma handles it, but 40k max size usually.
            # We are doing per book, usually < 5000 chunks.
            
            collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            print(f"  - Added {len(chunks)} chunks to ChromaDB.")
            
        except Exception as e:
            print(f"Error processing {file_name}: {e}")

    print("\nIngestion Complete.")
    print(f"Total Collection Size: {collection.count()} chunks.")

if __name__ == "__main__":
    main()
