import streamlit as st
import requests
import json
import uuid
import base64
import os

def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()
bg_image = get_base64_image("app/ui/background.jpg")

API_URL = os.environ.get("API_URL", "http://localhost:8000/chat")

st.set_page_config(
    page_title="CodeMentor AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(f"""
<style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{bg_image}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: #e6edf3;
    }}
    [data-testid="stSidebar"] {{ background-color: #161b22; border-right: 1px solid #30363d; }}
    [data-testid="stChatMessage"] {{ background-color: rgba(22, 27, 34, 0.85); border: 1px solid #30363d; border-radius: 12px; padding: 12px; margin-bottom: 8px; backdrop-filter: blur(10px); }}
    code {{ background-color: #1c2128 !important; color: #79c0ff !important; border-radius: 6px; }}
    pre code {{ display: block; padding: 16px !important; border: 1px solid #30363d; }}
    .stButton button {{ background-color: #21262d; color: #e6edf3; border: 1px solid #30363d; border-radius: 8px; }}
    .stButton button:hover {{ background-color: #30363d; border-color: #60a5fa; }}
</style>
""", unsafe_allow_html=True)

# session state
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "history" not in st.session_state:
    st.session_state.history = []

# sidebar
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 20px 0 10px 0;'>
        <div style='font-size: 2rem;'>🤖</div>
        <div style='font-size: 1.3rem; font-weight: 700; color: #e6edf3; margin-top: 8px;'>CodeMentor AI</div>
        <div style='font-size: 0.75rem; color: #8b949e; margin-top: 4px;'>Adaptive Python Code Review</div>
    </div>
    <hr style='border-color: #30363d; margin: 8px 0;'>
    <div style='padding: 4px 0 8px 0;'>
        <div style='font-size: 0.7rem; font-weight: 600; color: #8b949e; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 10px;'>Capabilities</div>
        <div style='background: #1c2128; border: 1px solid #30363d; border-radius: 8px; padding: 10px 12px; margin-bottom: 6px;'>
            <span style='color: #60a5fa;'>🔍</span>
            <span style='color: #e6edf3; font-size: 0.85rem; margin-left: 8px;'>Real linting via pylint</span>
        </div>
        <div style='background: #1c2128; border: 1px solid #30363d; border-radius: 8px; padding: 10px 12px; margin-bottom: 6px;'>
            <span style='color: #a78bfa;'>📚</span>
            <span style='color: #e6edf3; font-size: 0.85rem; margin-left: 8px;'>RAG over Python docs</span>
        </div>
        <div style='background: #1c2128; border: 1px solid #30363d; border-radius: 8px; padding: 10px 12px; margin-bottom: 6px;'>
            <span style='color: #34d399;'>✅</span>
            <span style='color: #e6edf3; font-size: 0.85rem; margin-left: 8px;'>Automated test execution</span>
        </div>
        <div style='background: #1c2128; border: 1px solid #30363d; border-radius: 8px; padding: 10px 12px; margin-bottom: 6px;'>
            <span style='color: #f59e0b;'>🧠</span>
            <span style='color: #e6edf3; font-size: 0.85rem; margin-left: 8px;'>Knowledge gap tracking</span>
        </div>
        <div style='background: #1c2128; border: 1px solid #30363d; border-radius: 8px; padding: 10px 12px; margin-bottom: 6px;'>
            <span style='color: #f87171;'>🛡️</span>
            <span style='color: #e6edf3; font-size: 0.85rem; margin-left: 8px;'>Prompt injection defense</span>
        </div>
    </div>
    <hr style='border-color: #30363d; margin: 8px 0;'>
    <div style='font-size: 0.7rem; font-weight: 600; color: #8b949e; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px;'>How to use</div>
    <div style='font-size: 0.8rem; color: #8b949e; line-height: 1.6;'>
        Paste Python code or ask a question. The agent lints your code, searches official docs, and runs tests automatically.
    </div>
    <hr style='border-color: #30363d; margin: 8px 0;'>
    <div style='font-size: 0.7rem; font-weight: 600; color: #8b949e; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px;'>Tech Stack</div>
    <div style='display: flex; flex-wrap: wrap; gap: 6px;'>
        <span style='background: #1c2128; border: 1px solid #30363d; border-radius: 20px; padding: 3px 10px; font-size: 0.7rem; color: #60a5fa;'>LangGraph</span>
        <span style='background: #1c2128; border: 1px solid #30363d; border-radius: 20px; padding: 3px 10px; font-size: 0.7rem; color: #a78bfa;'>ChromaDB</span>
        <span style='background: #1c2128; border: 1px solid #30363d; border-radius: 20px; padding: 3px 10px; font-size: 0.7rem; color: #34d399;'>PostgreSQL</span>
        <span style='background: #1c2128; border: 1px solid #30363d; border-radius: 20px; padding: 3px 10px; font-size: 0.7rem; color: #f59e0b;'>Groq</span>
        <span style='background: #1c2128; border: 1px solid #30363d; border-radius: 20px; padding: 3px 10px; font-size: 0.7rem; color: #f87171;'>RAGAS</span>
        <span style='background: #1c2128; border: 1px solid #30363d; border-radius: 20px; padding: 3px 10px; font-size: 0.7rem; color: #e6edf3;'>FastAPI</span>
    </div>
    <hr style='border-color: #30363d; margin: 8px 0;'>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='background: #1c2128; border: 1px solid #30363d; border-radius: 8px; padding: 10px 12px; margin-bottom: 12px;'>
        <div style='font-size: 0.7rem; color: #8b949e; margin-bottom: 4px;'>Session ID</div>
        <div style='font-size: 0.75rem; color: #60a5fa; font-family: monospace;'>{st.session_state.user_id[:20]}...</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.history = []
        st.rerun()

# main area
st.markdown("<h1 style='font-size: 2rem; font-weight: 700; background: linear-gradient(135deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>CodeMentor AI</h1>", unsafe_allow_html=True)
st.markdown("""
<div style="
    display: inline-block;
    background: rgba(22,27,34,0.85);
    border: 1px solid rgba(96,165,250,0.4);
    border-radius: 10px;
    padding: 8px 14px;
    margin-top: -10px;
    margin-bottom: 24px;
    backdrop-filter: blur(8px);
">
    <span style="
        color: #e6edf3;
        font-size: 1rem;
        font-weight: 500;
    ">
        Adaptive Python code review powered by
        <span style="color:#60a5fa;">RAG</span>,
        <span style="color:#a78bfa;">tools</span>,
        and
        <span style="color:#34d399;">persistent memory</span>
    </span>
</div>
""", unsafe_allow_html=True)

# conversation history
for entry in st.session_state.history:
    with st.chat_message("user", avatar="👤"):
        st.markdown(entry["user_message"])
    with st.chat_message("assistant", avatar="🤖"):
        if entry.get("tool_log"):
            with st.expander("🔧 Tool call details", expanded=False):
                for log_entry in entry["tool_log"]:
                    st.markdown(log_entry)
        st.markdown(entry["final_answer"])

# chat input
user_input = st.chat_input("Paste your Python code or ask a question...")

if user_input:
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🤖"):
        tool_placeholder = st.empty()
        answer_placeholder = st.empty()

        final_answer = ""
        tool_log = []
        tool_detail_lines = []

        try:
            response = requests.post(
                API_URL,
                json={"message": user_input, "user_id": st.session_state.user_id},
                stream=True,
                timeout=120
            )

            for line in response.iter_lines():
                if not line:
                    continue
                line_str = line.decode("utf-8")
                if not line_str.startswith("data: "):
                    continue

                event = json.loads(line_str[len("data: "):])

                if event["type"] == "tool_call":
                    tools_str = ", ".join(f"`{t}`" for t in event["tools"])
                    tool_log.append(f"⚙️ Calling: {tools_str}")
                    tool_detail_lines.append(f"⚙️ **Calling:** {tools_str}")
                    tool_placeholder.info(" · ".join(tool_log))

                elif event["type"] == "tool_result":
                    tool_name = event["tool"]
                    tool_log.append(f"✅ {tool_name} done")
                    tool_detail_lines.append(f"✅ **{tool_name} result:**\n```\n{event['content']}\n```")
                    tool_placeholder.info(" · ".join(tool_log))

                elif event["type"] == "final_answer":
                    final_answer = event["content"]
                    tool_placeholder.empty()
                    answer_placeholder.markdown(final_answer)

                elif event["type"] == "error":
                    tool_placeholder.empty()
                    answer_placeholder.warning(event["content"])
                    final_answer = event["content"]

        except requests.exceptions.ConnectionError:
            answer_placeholder.error("Could not connect to the API. Make sure FastAPI is running on port 8000.")
            final_answer = "Error: API not reachable."
        except Exception as e:
            answer_placeholder.error(f"An error occurred: {e}")
            final_answer = f"Error: {e}"

        if tool_detail_lines:
            with st.expander("🔧 Tool call details", expanded=False):
                for line in tool_detail_lines:
                    st.markdown(line)
                    st.markdown("---")

    st.session_state.history.append({
        "user_message": user_input,
        "final_answer": final_answer,
        "tool_log": tool_detail_lines
    })