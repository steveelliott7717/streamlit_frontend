import logging
import streamlit as st
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up the title
st.set_page_config(
    page_title="Reminisc - Personal Memory for AI", layout="wide", page_icon="🧠")
st.title("🧠 Reminisc")
st.info('')

user_id = st.text_input("Enter a User ID",
                        value=st.session_state.get("user_id"))
st.session_state["user_id"] = user_id

openai_api_key = st.text_input("Enter your OpenAI API Key", type="password", value=st.session_state.get(
    "openai_api_key"))
st.session_state["openai_api_key"] = openai_api_key
headers = {"Content-Type": "application/json",
           "openai-api-key": st.session_state.openai_api_key}

# API endpoint URLs
BASE_URL = "https://reminisc.fly.dev/v0/memory"
CREATE_MEMORY_URL = f"{BASE_URL}/"
GET_MEMORIES_URL = f"{BASE_URL}/"
DELETE_MEMORY_URL = f"{BASE_URL}/"
SEARCH_MEMORIES_URL = f"{BASE_URL}/search"
PROCESS_INPUT_URL = f"{BASE_URL}/process"

# Nothing here anymore — all GPT handling is in the backend now


# Check and manage the session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Create two columns: one for chat and one for memory management
chat_column, memory_column = st.columns(2)

with chat_column:
    st.header("Talk to Rem")

    # Create an empty container for the input bar
    input_container = st.empty()

    # Display the past conversation
    chat_history_container = st.container()

    # User input handling
    with input_container.container():
        if not st.session_state.openai_api_key or not st.session_state.user_id:
            chat_disabled = True
            chat_placeholder = "Enter your OpenAI API Key and a User ID to chat"
        else:
            chat_disabled = False
            chat_placeholder = "What is up?"

        prompt = st.chat_input(chat_placeholder, disabled=chat_disabled)
        if prompt:
            if not st.session_state.openai_api_key:
                st.error(
                    "Enter your OpenAI API Key. You can get it from here: https://platform.openai.com/api-keys")
                st.stop()

            st.session_state.messages.append(
                {"role": "user", "content": prompt})
            with chat_history_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            # Process the input and manage memory using API requests
            response = requests.post(PROCESS_INPUT_URL, json={
                "query": prompt, "user_id": user_id}, headers=headers)
            process_response = response.json()
            memory = process_response["content"]

            # Search for relevant memories using API request
            response = requests.post(
                SEARCH_MEMORIES_URL, json={"query": prompt, "user_id": user_id}, headers=headers)
            search_results = response.json()
            relevant_memory = " ".join(
                [memory["content"] for memory in search_results])
            # Just use backend's processed memory content as assistant reply
            response_text = memory


            with chat_history_container:
                if memory:
                    with st.expander("📝 Memory updated"):
                        st.write(memory)
                with st.chat_message("assistant", avatar="🧠"):
                    response_text = st.write_stream(stream)

            logger.info(f"User Input: {prompt}")
            logger.info(f"Generated Response: {response_text}")

            # Save the assistant's response in the session
            st.session_state.messages.append(
                {"role": "assistant", "content": response_text})

with memory_column:
    st.header("Manage Memories")

    if st.session_state.user_id and st.session_state.openai_api_key:
        # Display all memories using API request
        response = requests.get(GET_MEMORIES_URL, params={
                                "user_id": user_id}, headers=headers)
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
                    requests.delete(
                        f"{DELETE_MEMORY_URL}{memory_id}", headers=headers)
                    st.rerun()

        with st.expander("✍️ Create New Memory"):
            if not st.session_state.openai_api_key:
                memory_placeholder = "Enter your OpenAI API Key to store memories"
                memory_disabled = True
            else:
                memory_placeholder = "Enter a new memory"
                memory_disabled = False

            new_memory = st.text_area(
                memory_placeholder, disabled=memory_disabled)
            if st.button("Store Memory", disabled=memory_disabled):
                requests.post(CREATE_MEMORY_URL, json={
                    "content": new_memory, "user_id": user_id}, headers=headers)
                st.rerun()
    else:
        st.warning("Enter your OpenAI API Key and a User ID to manage memories")
