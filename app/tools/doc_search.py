from app.rag.retriever import retrieve, format_context


def search_docs(query: str, k: int = 3) -> dict:
    """
    searches the Python docs ChromaDB collection.
    wraps the retriever with a cleaner interface for agent tool use.
    """
    try:
        chunks = retrieve(query, k=k)

        if not chunks:
            return {
                "success": True,
                "found": False,
                "results": [],
                "summary": "No relevant documentation found for this query."
            }

        return {
            "success": True,
            "found": True,
            "results": chunks,
            "formatted_context": format_context(chunks),
            "summary": f"Found {len(chunks)} relevant documentation sections."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "summary": f"Doc search failed: {e}"
        }


if __name__ == "__main__":
    result = search_docs("how to handle exceptions in Python")
    print(result["summary"])
    print("\nformatted context:")
    print(result["formatted_context"])