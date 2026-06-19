from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from app.agent.agent import build_agent_graph
from app.memory.memory_manager import ensure_user_exists, save_review
from app.guardrails.input_guardrails import validate_input
from app.guardrails.output_guardrails import validate_output
import json
from app.observability.logger import log_request, log_tool_call, log_response, log_error, log_guardrail_block
import time

app = FastAPI(title="CodeMentor AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_graph = build_agent_graph()


class ChatRequest(BaseModel):
    message: str
    user_id: str


@app.get("/")
def health_check():
    return {"status": "CodeMentor AI is running"}

@app.post("/chat")
def chat(request: ChatRequest):
    request_start = time.time()

    # input guardrail
    is_safe, error_message = validate_input(request.message)
    if not is_safe:
        log_guardrail_block(request.user_id, request.message, error_message)
        def blocked_stream():
            event = {"type": "final_answer", "content": error_message}
            yield f"data: {json.dumps(event)}\n\n"
        return StreamingResponse(blocked_stream(), media_type="text/event-stream")

    log_request(request.user_id, request.message)
    ensure_user_exists(request.user_id)

    def event_stream():
        collected_lint_result = None
        final_answer = ""
        tools_used = []

        try:
            for step in agent_graph.stream(
                {
                    "messages": [HumanMessage(content=request.message)],
                    "user_id": request.user_id
                },
                stream_mode="updates"
            ):
                for node_name, node_output in step.items():
                    messages = node_output.get("messages", [])
                    for msg in messages:
                        event = format_message_event(node_name, msg)
                        if event:
                            yield f"data: {json.dumps(event)}\n\n"

                        if event and event["type"] == "final_answer":
                            final_answer = event["content"]

                        if node_name == "tools":
                            tool_name = getattr(msg, "name", "unknown")
                            tool_start = time.time()
                            tool_duration = (time.time() - tool_start) * 1000
                            log_tool_call(tool_name, msg.content[:200], tool_duration)
                            tools_used.append(tool_name)

                        if node_name == "tools" and getattr(msg, "name", None) == "lint_code":
                            collected_lint_result = parse_lint_summary(msg.content)

            # output guardrail
            if final_answer:
                is_valid, warning = validate_output(final_answer)
                if not is_valid:
                    warning_event = {"type": "error", "content": warning}
                    yield f"data: {json.dumps(warning_event)}\n\n"

            total_duration = (time.time() - request_start) * 1000
            log_response(request.user_id, len(final_answer), total_duration, tools_used)

            if collected_lint_result is not None:
                save_review(request.user_id, request.message, collected_lint_result)

        except Exception as e:
            log_error("agent_error", str(e), {"user_id": request.user_id})
            error_event = {
                "type": "error",
                "content": "The agent encountered an issue generating a response. Please try rephrasing your request or simplifying the code."
            }
            yield f"data: {json.dumps(error_event)}\n\n"
            if collected_lint_result is not None:
                save_review(request.user_id, request.message, collected_lint_result)

    return StreamingResponse(event_stream(), media_type="text/event-stream")

def parse_lint_summary(summary_text: str) -> dict:
    import re
    result = {"errors": [], "warnings": [], "conventions": []}
    pattern = r"\[([a-z-]+)\]"
    section = None
    for line in summary_text.split("\n"):
        if line.startswith("Errors"):
            section = "errors"
        elif line.startswith("Warnings"):
            section = "warnings"
        elif line.startswith("Conventions") or line.startswith("Refactor"):
            section = "conventions"
        elif section and "[" in line:
            match = re.search(pattern, line)
            if match:
                result[section].append({"symbol": match.group(1)})
    return result


def format_message_event(node_name: str, msg) -> dict | None:
    if node_name == "agent":
        if getattr(msg, "tool_calls", None):
            tool_names = [tc["name"] for tc in msg.tool_calls]
            return {"type": "tool_call", "tools": tool_names}
        if msg.content:
            return {"type": "final_answer", "content": msg.content}

    if node_name == "tools":
        return {
            "type": "tool_result",
            "tool": getattr(msg, "name", "unknown"),
            "content": msg.content[:500]
        }

    return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)