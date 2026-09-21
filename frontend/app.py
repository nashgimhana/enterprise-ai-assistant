import os

import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Enterprise AI Assistant", page_icon="AI", layout="wide")
st.title("Enterprise AI Assistant")

if "token" not in st.session_state:
    st.session_state.token = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "activity" not in st.session_state:
    st.session_state.activity = []
if "role" not in st.session_state:
    st.session_state.role = None


with st.sidebar:
    st.header("Login")
    username = st.text_input("Username", value="viewer")
    password = st.text_input("Password", value="viewer123", type="password")
    if st.button("Sign in", use_container_width=True):
        try:
            response = requests.post(
                f"{BACKEND_URL}/login",
                json={"username": username, "password": password},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            st.session_state.token = data["token"]
            st.session_state.role = data["role"]
            st.session_state.messages = []
            st.session_state.activity = [f"Signed in as {data['username']} ({data['role']})"]
            st.rerun()
        except requests.RequestException as exc:
            st.error(f"Login failed: {exc}")

    st.divider()
    st.subheader("Demo Users")
    st.caption("viewer / viewer123")
    st.caption("analyst / analyst123")
    st.caption("admin / admin123")

left, right = st.columns([2, 1])

with left:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.session_state.token is None:
        st.info("Sign in from the sidebar to start chatting.")
    elif prompt := st.chat_input("Ask about incidents, runbooks, policies, or architecture"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            response = requests.post(
                f"{BACKEND_URL}/chat",
                json={"message": prompt},
                headers={"Authorization": f"Bearer {st.session_state.token}"},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            answer = data["answer"]
            if data["citations"]:
                sources = "\n".join(
                    f"- `{item['document_id']}` {item['title']} ({item['source']})"
                    for item in data["citations"]
                )
                answer = f"{answer}\n\n**Sources**\n{sources}"

            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.session_state.activity = data["activity"]
            with st.chat_message("assistant"):
                st.markdown(answer)
        except requests.HTTPError as exc:
            detail = exc.response.text if exc.response is not None else str(exc)
            st.error(f"Request failed: {detail}")
        except requests.RequestException as exc:
            st.error(f"Backend unavailable: {exc}")

with right:
    st.subheader("Agent Activity")
    role = st.session_state.role or "not signed in"
    st.caption(f"Current role: {role}")
    for item in st.session_state.activity:
        st.write(f"- {item}")
