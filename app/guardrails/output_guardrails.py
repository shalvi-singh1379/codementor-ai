MIN_RESPONSE_LENGTH = 50  # minimum characters for a valid response

HALLUCINATION_SIGNALS = [
    "as an ai language model",
    "i don't have access to",
    "i cannot browse the internet",
    "as of my knowledge cutoff",
    "i'm not able to view",
]


def check_response_length(response: str) -> tuple[bool, str]:
    """
    checks if the response is suspiciously short.
    returns (is_valid, reason_if_invalid)
    """
    if not response or len(response.strip()) < MIN_RESPONSE_LENGTH:
        return False, "The agent produced an incomplete response. Please try again."
    return True, ""


def check_hallucination_signals(response: str) -> tuple[bool, str]:
    """
    checks for common phrases that indicate the model is
    confusing its role or breaking character.
    returns (is_valid, warning_message_or_empty)
    """
    response_lower = response.lower()
    for signal in HALLUCINATION_SIGNALS:
        if signal in response_lower:
            return False, "Note: The response contained some uncertain language. Consider rephrasing your question."
    return True, ""


def validate_output(response: str) -> tuple[bool, str]:
    """
    runs all output guardrails.
    returns (is_valid, error_or_warning_message)
    """
    is_valid, reason = check_response_length(response)
    if not is_valid:
        return False, reason

    is_valid, reason = check_hallucination_signals(response)
    if not is_valid:
        return False, reason

    return True, ""