import streamlit as st
import os
import tempfile
from PyPDF2 import PdfReader
import tiktoken
from openai import OpenAI
from openai import OpenAIError

# ------------------ Setup ------------------ #
st.set_page_config(page_title="PulseShiftAI - Chatbot", page_icon="🤖", layout="centered")

openai_api_key = st.secrets["openai"]["api_key"]
POLYGON_API_KEY = st.secrets["polygon"]["api_key"]

client = OpenAI(api_key=openai_api_key)

# ------------------ CSS Styling ------------------ #
st.markdown("""
    <style>
    .chat-container {
        max-width: 800px;
        margin: auto;
        padding: 20px;
        border-radius: 1rem;
        background-color: #1e1e2f;
        box-shadow: 0px 0px 20px rgba(0, 255, 255, 0.1);
    }
    .chat-bubble-user {
        background-color: #0059ff;
        color: white;
        padding: 10px 15px;
        border-radius: 1rem 1rem 0 1rem;
        margin: 10px 0;
        text-align: right;
        width: fit-content;
        margin-left: auto;
    }
    .chat-bubble-bot {
        background-color: #2c2c3c;
        color: #00ffcc;
        padding: 10px 15px;
        border-radius: 1rem 1rem 1rem 0;
        margin: 10px 0;
        width: fit-content;
        margin-right: auto;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center;'>🤖 PulseShiftAI - Intelligence Chatbot</h2>", unsafe_allow_html=True)
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

# ------------------ Session State ------------------ #
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "context_docs" not in st.session_state:
    st.session_state.context_docs = ""

# ------------------ PDF Upload ------------------ #
with st.expander("📄 Upload Financial Document (PDF only)", expanded=False):
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        pdf = PdfReader(tmp_path)
        text = ""
        pages_read = 0
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
                pages_read += 1

        if pages_read == 0:
            st.error("❌ No readable text found in this PDF. It may be scanned or image-based.")
            st.session_state.context_docs = ""
        else:
            st.session_state.context_docs = text
            st.success(f"✅ Document processed. Text extracted from {pages_read} page(s).")


# ------------------ Token Truncation ------------------ #
def truncate_text_to_token_limit(text, max_tokens=1500):
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = enc.encode(text)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    return enc.decode(tokens)

# ------------------ OpenAI Chat ------------------ #
def get_response(prompt, history, context=""):
    system_msg = {
        "role": "system",
        "content": "You are a financially literate assistant. Answer user queries with accuracy, macroeconomic insights, and professional tone. Make sure your responses are very well explained and should be readable by a wide audience, which will have mostly bankers and technology people."
    }

    messages = [system_msg]
    
    if context:
        context_msg = {
            "role": "system",
            "content": f"Use the following document context when answering:\n{truncate_text_to_token_limit(context)}"
        }
        messages.append(context_msg)

    messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except OpenAIError as e:
        return f"⚠️ Error: {str(e)}"

# ------------------ Chat UI ------------------ #
for msg in st.session_state.chat_history:
    role = msg["role"]
    bubble_class = "chat-bubble-user" if role == "user" else "chat-bubble-bot"
    st.markdown(f"<div class='{bubble_class}'>{msg['content']}</div>", unsafe_allow_html=True)

# ------------------ Input ------------------ #
with st.form("chat_input_form", clear_on_submit=True):
    user_prompt = st.text_input("Ask your question (macro, markets, FX...)", key="chat_input")
    submitted = st.form_submit_button("Send")

if submitted and user_prompt.strip():
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})
    with st.spinner("Thinking..."):
        reply = get_response(user_prompt, st.session_state.chat_history, st.session_state.context_docs)
    st.session_state.chat_history.append({"role": "assistant", "content": reply})
    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ------------------ Optional Navigation ------------------ #
if st.button("🔙 Back to Home"):
    st.switch_page("Home.py")
