import re


# known prompt injection patterns
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"forget\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"you\s+are\s+now\s+a\s+different",
    r"new\s+persona",
    r"act\s+as\s+(if\s+you\s+are\s+)?(?!a\s+code)",  # "act as X" but not "act as a code reviewer"
    r"your\s+new\s+instructions",
    r"override\s+(your\s+)?(previous\s+)?instructions",
    r"system\s+prompt",
    r"reveal\s+your\s+(system\s+)?prompt",
    r"what\s+are\s+your\s+instructions",
    r"jailbreak",
    r"dan\s+mode",
]

# keywords that suggest the request is off-topic for a code review tool
OFF_TOPIC_PATTERNS = [
    r"\b(weather|forecast|temperature)\b",
    r"\b(stock|price|market|crypto|bitcoin)\b",
    r"\b(recipe|cook|food|restaurant)\b",
    r"\b(movie|film|song|music|celebrity)\b",
    r"\b(politics|election|president|government)\b",
    r"\b(essay|poem|story|novel|write\s+me\s+a)\b",
    r"\b(translate|translation)\b",
    r"\b(joke|humor|funny)\b",
]

# code review related keywords — presence of these overrides off-topic detection
CODE_REVIEW_KEYWORDS = [
    r"\b(code|function|class|method|variable|bug|error|exception|import)\b",
    r"\b(python|java|javascript|typescript|review|debug|fix|refactor)\b",
    r"\b(def|return|while|try|except|import)\b",
    r"\bfor\s+\w+\s+in\b",  # only match Python for loops: "for x in"
    r"\bif\s+.+[:=]",       # only match Python if statements with colon or comparison
    r"\bwith\s+\w+",        # only match Python with statements
    r"\bfrom\s+\w+\s+import\b",  # only match Python from...import
]


def check_prompt_injection(text: str) -> tuple[bool, str]:
    """
    checks if the input contains prompt injection attempts.
    returns (is_safe, reason_if_unsafe)
    """
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return False, f"Potential prompt injection detected. CodeMentor AI only reviews Python code and answers programming questions."
    return True, ""


def check_off_topic(text: str) -> tuple[bool, str]:
    """
    checks if the input is clearly off-topic for a code review tool.
    returns (is_on_topic, reason_if_off_topic)
    """
    text_lower = text.lower()

    # if it contains code review keywords, it's on-topic regardless
    has_code_keywords = any(
        re.search(pattern, text_lower, re.IGNORECASE)
        for pattern in CODE_REVIEW_KEYWORDS
    )
    if has_code_keywords:
        return True, ""

    # if NO code keywords AND at least one off-topic pattern matches — block it
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return False, "This request appears to be outside CodeMentor AI's scope. I'm specialized in Python code review, debugging, and programming questions. Please paste some code or ask a Python-related question!"

    return True, ""

def validate_input(text: str) -> tuple[bool, str]:
    """
    runs all input guardrails.
    returns (is_safe, error_message_if_unsafe)
    """
    # check length — reject empty or suspiciously short inputs
    if not text or len(text.strip()) < 5:
        return False, "Please provide a code snippet or programming question for me to review."

    # check for prompt injection
    is_safe, reason = check_prompt_injection(text)
    if not is_safe:
        return False, reason

    # check for off-topic content
    is_on_topic, reason = check_off_topic(text)
    if not is_on_topic:
        return False, reason

    return True, ""