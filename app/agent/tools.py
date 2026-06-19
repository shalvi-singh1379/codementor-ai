from langchain_core.tools import tool
from app.tools.linter import run_linter
from app.tools.test_runner import run_tests
from app.tools.doc_search import search_docs


@tool
def lint_code(code: str) -> str:
    """
    Runs pylint on the provided Python code and returns issues found.
    Use this to check code for errors, warnings, and style issues.
    
    Args:
        code: The Python code to lint as a string.
    """
    result = run_linter(code)
    return result["summary"]


@tool
def search_python_docs(query: str) -> str:
    """
    Searches official Python documentation for relevant information.
    Use this when you need to verify correct usage of a function, module,
    or Python feature, or to cite documentation in your review.
    
    Args:
        query: The search query, e.g. "how to use context managers"
    """
    result = search_docs(query, k=3)
    if not result["found"]:
        return result["summary"]
    return result["formatted_context"]


@tool
def run_python_tests(test_code: str, source_code: str = "") -> str:
    """
    Runs pytest on the provided test code, optionally with source code.
    Use this to verify that generated tests pass or to check if code works correctly.
    
    Args:
        test_code: The pytest/unittest test code as a string.
        source_code: Optional source code that the tests depend on.
    """
    result = run_tests(test_code, source_code)
    return result["summary"]


ALL_TOOLS = [lint_code, search_python_docs, run_python_tests]