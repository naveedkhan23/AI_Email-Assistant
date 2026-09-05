"""
AI Email Writer — Streamlit + Groq API
----------------------------------------
A single-file conversational email drafting assistant, streamed live.

Local run:
    streamlit run app.py

Deployment (Streamlit Community Cloud):
    1. Push this repo to GitHub (app.py + requirements.txt).
    2. On share.streamlit.io, create a new app pointing at this repo.
    3. In the app's Settings -> Secrets, add:
           GROQ_API_KEY = "gsk_..."
    The app reads it automatically at runtime via st.secrets.

API key resolution order: Streamlit secrets > GROQ_API_KEY env var > sidebar input.
"""

import os
import logging
import streamlit as st
from groq import Groq

# --------------------------------------------------------------------
# Silence background noise (Streamlit / httpx / groq SDK loggers)
# --------------------------------------------------------------------
logging.getLogger("streamlit").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)

st.set_page_config(page_title="AI Email Writer", page_icon="✉️", layout="centered")

# --------------------------------------------------------------------
# Resolve a default API key: Streamlit secrets first (how Streamlit Cloud
# injects it), then the environment variable, then nothing (user must
# paste it in the sidebar).
# --------------------------------------------------------------------
def _default_api_key() -> str:
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.environ.get("GROQ_API_KEY", "")

# --------------------------------------------------------------------
# Sidebar — API key + generation controls
# --------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    api_key = st.text_input(
        "Groq API Key",
        value=_default_api_key(),
        type="password",
        help="Set via Streamlit Secrets when deployed, or paste here for local testing. "
             "Get a free key at console.groq.com/keys",
    )

    model = st.selectbox(
        "Model",
        ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
    )
    tone = st.selectbox(
        "Tone",
        ["Professional", "Friendly", "Formal", "Persuasive", "Casual", "Assertive"],
    )
    purpose = st.selectbox(
        "Email Purpose",
        ["General", "Follow-up", "Sales Outreach", "Job Application",
         "Customer Support", "Meeting Request", "Thank You", "Complaint"],
    )
    length_words = st.select_slider(
        "Target Length", options=[75, 150, 300],
        format_func=lambda w: f"{w} words", value=150,
    )
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.05)

    # reasoning_effort is only supported by Groq's GPT-OSS models
    reasoning_effort = None
    if model == "openai/gpt-oss-120b":
        reasoning_effort = st.select_slider(
            "Reasoning Effort", options=["low", "medium", "high"], value="medium"
        )

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_draft = ""
        st.rerun()

# --------------------------------------------------------------------
# Session state — conversation history + latest draft for export
# --------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_draft" not in st.session_state:
    st.session_state.last_draft = ""

# --------------------------------------------------------------------
# Main UI
# --------------------------------------------------------------------
st.title("✉️ AI Email Writer")
st.caption("Describe the email you need, then ask for edits in follow-up messages.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if st.session_state.last_draft:
    with st.expander("📋 Latest draft — copy or download"):
        st.code(st.session_state.last_draft, language="text")
        st.download_button(
            "⬇️ Download as .txt", data=st.session_state.last_draft,
            file_name="email_draft.txt", mime="text/plain", use_container_width=True,
        )

user_prompt = st.chat_input("e.g. 'Write a follow-up after a job interview' or 'make it shorter'")

if user_prompt:
    if not api_key:
        st.error("⚠️ Enter your Groq API key in the sidebar (or set it in Secrets) to continue.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # System prompt rebuilt fresh each turn so sidebar changes apply immediately
    system_prompt = (
        f"You are an expert email-writing assistant. Tone: {tone}. "
        f"Purpose: {purpose}. Target length: ~{length_words} words. "
        "Start with 'Subject: ...' then a blank line then the email body. "
        "If asked to revise, edit the previous draft rather than starting over. "
        "Output only the subject and body — no extra commentary."
    )
    messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        try:
            client = Groq(api_key=api_key)

            kwargs = dict(
                model=model,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=2048,
                top_p=1,
                stream=True,
                stop=None,
            )
            if reasoning_effort:
                kwargs["reasoning_effort"] = reasoning_effort

            completion = client.chat.completions.create(**kwargs)

            for chunk in completion:
                full_response += chunk.choices[0].delta.content or ""
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)

        except Exception as e:
            # Groq SDK errors (auth, rate limit, connection, etc.) all land here;
            # classify by message text since we don't import specific error classes.
            err_text = str(e).lower()
            full_response = ""
            if "401" in err_text or "invalid api key" in err_text or "authentication" in err_text:
                placeholder.error("🔑 Invalid Groq API key. Check the key in the sidebar or Secrets.")
            elif "429" in err_text or "rate limit" in err_text:
                placeholder.error("⏳ Rate limit hit. Wait a moment or switch models.")
            elif "connection" in err_text:
                placeholder.error("📡 Couldn't reach the Groq API. Check your connection.")
            else:
                placeholder.error(f"❌ Error: {e}")

    if full_response:
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.last_draft = full_response
        st.rerun()
