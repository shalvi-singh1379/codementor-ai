import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "codementor.jsonl"


def get_logger():
    """returns a configured logger that writes JSON to file and text to console"""
    logger = logging.getLogger("codementor")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # file handler — structured JSON, one event per line
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    # console handler — human readable
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def log_event(event_type: str, data: dict):
    """
    logs a structured JSON event to file.
    every event gets a timestamp automatically.
    """
    logger = get_logger()

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        **data
    }

    logger.info(json.dumps(event))


def log_request(user_id: str, message: str):
    log_event("request", {
        "user_id": user_id,
        "message_length": len(message),
        "message_preview": message[:100]
    })


def log_tool_call(tool_name: str, result_preview: str, duration_ms: float):
    log_event("tool_call", {
        "tool_name": tool_name,
        "result_preview": result_preview[:200],
        "duration_ms": round(duration_ms, 2)
    })


def log_response(user_id: str, response_length: int, duration_ms: float, tool_calls: list):
    log_event("response", {
        "user_id": user_id,
        "response_length": response_length,
        "duration_ms": round(duration_ms, 2),
        "tools_used": tool_calls
    })


def log_error(error_type: str, error_message: str, context: dict = {}):
    log_event("error", {
        "error_type": error_type,
        "error_message": str(error_message)[:500],
        "context": context
    })


def log_guardrail_block(user_id: str, message: str, reason: str):
    log_event("guardrail_block", {
        "user_id": user_id,
        "message_preview": message[:100],
        "reason": reason
    })