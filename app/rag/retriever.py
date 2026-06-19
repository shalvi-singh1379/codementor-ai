from app.rag.indexer import get_chroma_collection

TOP_K = 5  # number of chunks to retrieve per query


def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """
    takes a user query, finds the most similar chunks in ChromaDB.
    returns list of dicts with 'text' and 'metadata'.
    """
    collection = get_chroma_collection()
    
    results = collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )
    
    chunks = []
    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        chunks.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "relevance_score": round(1 - distance, 3)  # convert distance to similarity
        })
    
    return chunks


def format_context(chunks: list[dict]) -> str:
    """
    formats retrieved chunks into a clean context string
    to inject into the LLM prompt.
    """
    if not chunks:
        return "No relevant documentation found."
    
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Doc {i} | Source: {chunk['source']} | Relevance: {chunk['relevance_score']}]\n"
            f"{chunk['text']}"
        )
    
    return "\n\n---\n\n".join(context_parts)


if __name__ == "__main__":
    query = "how to use context managers in Python"
    chunks = retrieve(query)
    print(f"retrieved {len(chunks)} chunks for query: '{query}'\n")
    print(format_context(chunks))