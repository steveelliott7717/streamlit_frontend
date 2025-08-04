import logging
import streamlit as st
import requests
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up Streamlit page
st.set_page_config(
    page_title="Reminisc - Personal Memory for AI", layout="wide", page_icon="🧠")
st.title("🧠 Reminisc")
st.info('')

# User ID input
user_id = st.text_input("Enter a User ID", value=st.session_state.get("user_id"))
st.session_state["user_id"] = user_id

# Set OpenAI API key from environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
st.session_state["openai_api_key"] = OPENAI_API_KEY

# API headers and endpoints
headers = {
    "Content-Type": "application/json",
    "openai-api-key": OPENAI_API_KEY
}
BASE_URL = "https://reminisc.fly.dev/v0/memory"
CREATE_MEMORY_URL = f"{BASE_URL}/"
GET_MEMORIES_URL = f"{BASE_URL}/"
DELETE_MEMORY_URL = f"{BASE_URL}/"
SEARCH_MEMORIES_URL = f"{BASE_URL}/search"
PROCESS_INPUT_URL = f"{BASE_URL}/process"

# Session messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Layout: Chat and Memory columns
chat_column, memory_column = st.columns(2)

with chat_column:
    st.header("Talk to Rem")
    input_container = st.empty()
    chat_history_container = st.container()

    with input_container.container():
        chat_disabled = not (OPENAI_API_KEY and user_id)
        chat_placeholder = "What is up?" if not chat_disabled else "Enter a User ID to chat"

        prompt = st.chat_input(chat_placeholder, disabled=chat_disabled)
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})

            with chat_history_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            # Process input via backend
            response = requests.post(PROCESS_INPUT_URL, json={
                "query": prompt, "user_id": user_id
            }, headers=headers)
            process_response = response.json()
            memory = process_response.get("content", "")

            response_text = memory

            with chat_history_container:
                if memory:
                    with st.expander("📝 Memory updated"):
                        st.write(memory)
                with st.chat_message("assistant", avatar="🧠"):
                    st.markdown(response_text)

            logger.info(f"User Input: {prompt}")
            logger.info(f"Generated Response: {response_text}")

            st.session_state.messages.append(
                {"role": "assistant", "content": response_text}
            )

with memory_column:
    st.header("Manage Memories")

    if user_id and OPENAI_API_KEY:
        response = requests.get(GET_MEMORIES_URL, params={"user_id": user_id}, headers=headers)
        memories = response.json()

        for memory in memories:
            memory_id = memory["metadata"]["id"]
            timestamp = memory["metadata"]["timestamp"]
            memory_content = memory["content"]

            with st.expander(memory_content):
                st.write(f"**Memory ID:** {memory_id}")
                st.write(f"**Timestamp:** {timestamp}")
                st.write(f"**Memory:** {memory_content}")
                if st.button("Delete", key=memory_id):
                    requests.delete(f"{DELETE_MEMORY_URL}{memory_id}", headers=headers)
                    st.rerun()

        with st.expander("✍️ Create New Memory"):
            new_memory = st.text_area("Enter a new memory")
            if st.button("Store Memory"):
                requests.post(CREATE_MEMORY_URL, json={
                    "content": new_memory, "user_id": user_id
                }, headers=headers)
                st.rerun()
    else:
        st.warning("Enter a User ID to manage memories.")
