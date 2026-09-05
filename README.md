# ✉️ AI Email Writer

Link Of My Project 
https://naveedkhan23-ai-email-assistant-app-myfkkl.streamlit.app/

A conversational email-drafting assistant built with **Streamlit** and the **Groq API**, with live token streaming.

## Features

- Chat interface (`st.chat_message` + `st.chat_input`) with streaming responses
- Conversation memory — follow-ups like "make it shorter" revise the existing draft
- Sidebar controls: Model, Tone, Purpose, Target Length, Temperature, Reasoning Effort
- Error handling for invalid API keys, rate limits, and connection issues
- Copy (via built-in code-block icon) or download the latest draft as `.txt`

## Project Structure

```
.
├── app.py
├── requirements.txt
└── README.md
```

## 1. Run Locally

```bash
pip install -r requirements.txt
export GROQ_API_KEY="gsk_..."      # or paste it in the sidebar at runtime
streamlit run app.py
```

Get a free key at [console.groq.com/keys](https://console.groq.com/keys).

## 2. Push to GitHub

```bash
git init
git add app.py requirements.txt README.md
git commit -m "AI Email Writer"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

**Do not commit your API key.** Never put it in `app.py` or a `secrets.toml` that gets pushed. If you use a local `.streamlit/secrets.toml` for testing, add this to `.gitignore`:

```
.streamlit/secrets.toml
```

## 3. Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app**, select your repo, branch (`main`), and set the main file path to `app.py`.
3. Before (or after) deploying, open **Advanced settings → Secrets** and add:
   ```toml
   GROQ_API_KEY = "gsk_..."
   ```
4. Click **Deploy**. Streamlit installs `requirements.txt` automatically and starts the app.

The app reads the key in this order: **Streamlit Secrets → `GROQ_API_KEY` env var → sidebar input** — so once Secrets is set, no one needs to paste a key manually.

## Notes

- Default model is `openai/gpt-oss-120b`; `llama-3.3-70b-versatile` and `llama-3.1-8b-instant` are also selectable.
- "Reasoning Effort" only appears for `openai/gpt-oss-120b`, since it's a GPT-OSS-specific parameter.
- Sidebar setting changes apply to the next message immediately — the system prompt is rebuilt fresh on every request.
