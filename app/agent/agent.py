from langgraph.graph import StateGraph, END, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
from app.agent.tools import ALL_TOOLS
import os
from dotenv import load_dotenv
from app.memory.memory_manager import get_active_knowledge_gaps, format_knowledge_gaps_for_prompt

from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str

load_dotenv()

MAX_ITERATIONS = 5

AGENT_SYSTEM_PROMPT = """You are CodeMentor AI, an expert Python code review agent.

You have access to these tools:
- lint_code: check code for errors, warnings, and style issues
- search_python_docs: search official Python documentation
- run_python_tests: run pytest on test code

When reviewing code:
1. First, lint the code to find concrete issues
2. If you're unsure about correct usage, search the docs
3. If the user wants tests, write them and run them to verify they work
4. Synthesize everything into a final structured review:
   - Summary of issues found
   - Detailed explanation (cite docs and lint results)
   - Improved code
   - Test results (if applicable)

Be precise and senior-engineer level. Don't call tools unnecessarily — 
if the code is simple and you're confident, you can skip straight to the review."""


def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        api_key=os.environ.get("GROQ_API_KEY"),
    ).bind_tools(ALL_TOOLS)


def agent_node(state: AgentState):
    """the 'brain' - LLM decides what to do next"""
    llm = get_llm()
    messages = state["messages"]
    user_id = state.get("user_id", "anonymous")

    if not any(m.type == "system" for m in messages):
        from langchain_core.messages import SystemMessage

        gaps = get_active_knowledge_gaps(user_id)
        gaps_context = format_knowledge_gaps_for_prompt(gaps)

        full_system_prompt = AGENT_SYSTEM_PROMPT
        if gaps_context:
            full_system_prompt += f"\n\n{gaps_context}"

        messages = [SystemMessage(content=full_system_prompt)] + messages

    response = llm.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState):
    """decides whether to call tools or end"""
    last_message = state["messages"][-1]

    # check iteration count
    tool_call_count = sum(
        1 for m in state["messages"] if getattr(m, "tool_calls", None)
    )
    if tool_call_count >= MAX_ITERATIONS:
        return "end"

    # if the LLM wants to call a tool, do it
    if getattr(last_message, "tool_calls", None):
        return "tools"

    return "end"


def build_agent_graph():
    """builds and compiles the LangGraph agent"""
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))

    graph.set_entry_point("agent")

    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        }
    )

    graph.add_edge("tools", "agent")

    return graph.compile()


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    app = build_agent_graph()

    user_code = """
def read_file(path):
    f = open(path)
    data = f.read()
    return data
"""

    user_message = f"Review this Python code:\n```python\n{user_code}\n```"

    print("running agent...\n")
    result = app.invoke({"messages": [HumanMessage(content=user_message)]})

    print("=== FINAL RESPONSE ===")
    print(result["messages"][-1].content)

    print("\n=== FULL MESSAGE TRACE ===")
    for msg in result["messages"]:
        print(f"\n[{msg.type}]")
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                print(f"  TOOL CALL: {tc['name']}({tc['args']})")
        if msg.content:
            print(f"  {msg.content[:300]}")