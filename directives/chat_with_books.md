# Chat with Books via RAG

## Goal
Enable an interactive chat session where the AI answers questions based *strictly* on the content of the text files provided in the `Books/` directory.

## Inputs
- User query (text)
- `Books/*.txt` (source material)

## Tools
- `execution/rag_chat.py`

## Protocol
1. **Ingestion (First Run)**:
   - Scan all `.txt` files in `Books/`.
   - Chunk content into manageable segments (e.g., ~1000 characters).
   - Generate embeddings for each chunk using OpenAI `text-embedding-3-small` (cost-effective and valid).
   - Store embeddings and chunks locally (e.g., in `.tmp/embeddings_cache.pkl`) to avoid re-incurring costs on every run.

2. **Retrieval**:
   - Embed the user's query.
   - Calculate cosine similarity between query embedding and chunk embeddings.
   - Retrieve top 5 most relevant chunks.

3. **Generation**:
   - Construct a system prompt: "You are a helpful assistant. Answer the user's question using ONLY the provided context."
   - specific instructions: Cite the source file if possible.
   - Call OpenAI `chat.completions.create` (GPT-5-mini or GPT-5-nano).

4. **Interaction**:
   - Run in a loop accepting user input until "exit" or "quit".
