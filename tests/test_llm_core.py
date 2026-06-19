import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.llm_core import stream_response, get_full_response

def test_streaming():
    print("\n--- testing streaming ---")
    user_message = "Review this Python code: def add(a,b): return a+b"
    
    print("streaming response: ", end="", flush=True)
    for token in stream_response(user_message):
        print(token, end="", flush=True)
    print("\n--- streaming test done ---")

def test_full_response():
    print("\n--- testing full response ---")
    response = get_full_response("What is a list comprehension in Python?")
    print(f"response length: {len(response)} characters")
    print(f"first 200 chars: {response[:200]}")
    print("--- full response test done ---")

if __name__ == "__main__":
    test_streaming()
    test_full_response()