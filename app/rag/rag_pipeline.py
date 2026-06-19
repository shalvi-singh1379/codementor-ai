import re
from app.rag.retriever import retrieve, format_context
from app.llm_core import stream_response, get_full_response

RAG_SYSTEM_PROMPT = """You are CodeMentor AI, an expert Python code review assistant.

You will be given:
1. RETRIEVED DOCUMENTATION: Relevant sections from the official Python docs
2. USER QUESTION: The user's code and/or question

CRITICAL RULES — YOU MUST FOLLOW THESE:
- You may ONLY cite documents that appear in the RETRIEVED DOCUMENTATION section
- Every Doc number you cite must exist in the retrieved context provided
- NEVER cite sources from your training data as if they were retrieved docs
- If the retrieved docs don't cover something, say "based on general Python best practices" NOT "according to Doc X"
- If you are not sure, say you are not sure — never invent a citation

Your job:
- Review the code using the retrieved documentation as your primary source
- Cite which doc source supports your feedback using ONLY the docs provided above
- Be precise, educational, and senior-engineer level
- Structure your response as:
  1. Summary of issues found
  2. Detailed explanation with doc references (only from retrieved docs)
  3. Improved code
  4. Suggested tests"""

def looks_like_code(text: str) -> bool:
    """
    heuristic check: does this message contain Python code,
    as opposed to being a plain natural-language question?
    """
    code_indicators = [
        r"\bdef\s+\w+\s*\(",      # function definitions
        r"\bclass\s+\w+",          # class definitions
        r"\bimport\s+\w+",         # imports
        r"\bfor\s+\w+\s+in\s+",    # for loops
        r"\btry\s*:",              # try blocks
        r"^\s{4,}\w+",             # indented lines (4+ spaces)
    ]
    return any(re.search(pattern, text, re.MULTILINE) for pattern in code_indicators)

def rewrite_query_for_retrieval(user_message: str) -> str:
    """
    if the input looks like code, generate a natural-language description
    of it to use for retrieval instead of the raw code. this bridges the
    modality gap between code syntax and prose documentation.
    """
    if not looks_like_code(user_message):
        return user_message  # already natural language, no rewrite needed

    rewrite_prompt = f"""Describe in one or two plain English sentences what 
this Python code does and what potential issues it might have. Do not 
write any code in your response, only a natural language description.

Code:
{user_message}"""

    description = get_full_response(
        user_message=rewrite_prompt,
        system_prompt="You are a helpful assistant that describes code in plain English.",
        temperature=0.3,
    )
    return description

def build_rag_prompt(user_message: str) -> str:
    """retrieves relevant docs and builds an augmented prompt"""
    chunks = retrieve(user_message)
    context = format_context(chunks)

    augmented_prompt = f"""RETRIEVED DOCUMENTATION:
{context}

USER QUESTION:
{user_message}"""

    return augmented_prompt


def rag_stream(user_message: str, conversation_history: list = []):
    """full RAG pipeline with streaming"""
    augmented_prompt = build_rag_prompt(user_message)

    for token in stream_response(
        user_message=augmented_prompt,
        conversation_history=conversation_history,
        system_prompt=RAG_SYSTEM_PROMPT
    ):
        yield token


def rag_query(user_message: str, conversation_history: list = []) -> str:
    """full RAG pipeline, returns complete response"""
    augmented_prompt = build_rag_prompt(user_message)

    return get_full_response(
        user_message=augmented_prompt,
        conversation_history=conversation_history,
        system_prompt=RAG_SYSTEM_PROMPT
    )


if __name__ == "__main__":
    question = """Review this Python code:

def read_file(path):
    f = open(path)
    data = f.read()
    return data
"""
    print("question:", question)
    print("\nCodeMentor AI response (RAG-powered):\n")
    print("-" * 50)

    for token in rag_stream(question):
        print(token, end="", flush=True)

    print("\n" + "-" * 50)