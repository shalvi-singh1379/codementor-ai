import os
import re
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
#from sentence_transformers import SentenceTransformer

# ----- configuration -----
DOCS_DIR = Path("data/docs")
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "python_docs"
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

_collection_cache = None

def get_chroma_collection():
    global _collection_cache
    if _collection_cache is not None:
        return _collection_cache

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    embedding_fn = embedding_functions.DefaultEmbeddingFunction()  # ONNX MiniLM-L6-v2, no torch needed

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )
    _collection_cache = collection
    return collection


def chunk_text(text: str, source_url: str) -> list[dict]:
    """
    splits text into overlapping chunks using character-based sliding window.
    """
    lines = text.split("\n")
    if lines[0].startswith("SOURCE:"):
        source_url = lines[0].replace("SOURCE:", "").strip()
        text = "\n".join(lines[2:])

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + CHUNK_SIZE, text_length)

        if end < text_length:
            newline_pos = text.rfind("\n", start, end)
            if newline_pos > start:
                end = newline_pos

        chunk = text[start:end].strip()
        if chunk:
            chunks.append({
                "text": chunk,
                "metadata": {
                    "source": source_url,
                    "chunk_index": len(chunks),
                    "total_chunks": 0
                }
            })

        new_start = end - CHUNK_OVERLAP
        if new_start <= start:  # prevent infinite loop
            new_start = start + CHUNK_SIZE
        start = new_start

    for chunk in chunks:
        chunk["metadata"]["total_chunks"] = len(chunks)

    return chunks


def index_docs():
    """main function: reads all txt files, chunks them, stores in ChromaDB"""
    collection = get_chroma_collection()

    existing = collection.count()
    if existing > 0:
        print(f"collection already has {existing} chunks. skipping indexing.")
        print("delete 'chroma_db/' folder to re-index.")
        return collection

    txt_files = list(DOCS_DIR.glob("*.txt"))
    print(f"found {len(txt_files)} doc files to index")

    all_chunks = []
    for txt_file in txt_files:
        if txt_file.name == "download_docs.py":
            continue
        with open(txt_file, "r", encoding="utf-8") as f:
            text = f.read()
        chunks = chunk_text(text, txt_file.name)
        all_chunks.extend(chunks)
        print(f"  chunked {txt_file.name}: {len(chunks)} chunks")

    print(f"\ntotal chunks to embed: {len(all_chunks)}")
    print("storing in ChromaDB (embeddings generated automatically)...")

    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        collection.add(
            documents=[c["text"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
            ids=[f"chunk_{i + j}" for j, _ in enumerate(batch)]
        )
        print(f"  stored batch {i//batch_size + 1}/{(len(all_chunks)-1)//batch_size + 1}")

    print(f"\ndone! {collection.count()} chunks stored in ChromaDB")
    return collection

if __name__ == "__main__":
    index_docs()