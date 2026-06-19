import os
from groq import Groq
from dotenv import load_dotenv
from typing import Generator

load_dotenv()

# ----- configuration -----
DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2048

SYSTEM_PROMPT = """You are CodeMentor AI, an expert code review assistant.
You help developers write better code by:
- Reviewing code for bugs, inefficiencies, and bad practices
- Explaining trade-offs between different approaches
- Suggesting improvements with clear reasoning
- Generating tests for submitted code
- Citing relevant documentation when helpful

Always structure your response as:
1. Summary of issues found
2. Detailed explanation of each issue
3. Improved code (if applicable)
4. Suggested tests (if applicable)

Be precise, educational, and senior-engineer level in your feedback."""


def get_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    return Groq(api_key=api_key)


def stream_response(
    user_message: str,
    conversation_history: list = [],
    system_prompt: str = SYSTEM_PROMPT,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> Generator[str, None, None]:
    """
    Streams response tokens from the LLM one by one.
    Returns a generator — caller iterates over it to get tokens.
    """
    client = get_client()

    messages = [{"role": "system", "content": system_prompt}]
    messages += conversation_history
    messages.append({"role": "user", "content": user_message})

    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )

    for chunk in stream:
        token = chunk.choices[0].delta.content
        if token is not None:
            yield token


def get_full_response(
    user_message: str,
    conversation_history: list = [],
    system_prompt: str = SYSTEM_PROMPT,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    Returns the complete response as a single string.
    Used when you need the full response before doing something with it
    (e.g. passing to evaluation pipeline).
    """
    full_response = ""
    for token in stream_response(
        user_message, conversation_history, system_prompt, model, temperature, max_tokens
    ):
        full_response += token
    return full_response