import streamlit as st
from backend_database import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage

import uuid  # to create random new thread IDs

# ************************************************* Utility functions**********************************

def generate_thread_id():
    """
    Generate a random unique thread ID using UUID.
    Each new chat session will be identified with this ID.
    """
    thread_id = uuid.uuid4()
    return thread_id  # type: ignore


def reset_chat():
    """
    Reset the chat:
    - Generate a new thread ID.
    - Store it in session state.
    - Add this thread to the list of chat threads.
    - Clear the current message history.
    """
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id  # store the new thread ID
    add_thread(st.session_state['thread_id'])  # add the new thread to chat threads
    st.session_state['message_history'] = []   # clear message history for fresh chat


def add_thread(thread_id):
    """
    Add a thread ID to session state chat_threads
    if it doesn't already exist.
    """
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)


def load_conversation(thread_id):
    """
    Load all messages of a given thread ID from the chatbot state.
    Returns a list of messages if present, otherwise returns an empty list.
    """
    # >>> Added for Suggestion 1: Error Handling
    try:
        state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
        # Retrieve messages from state (default to [] if not found)
        return state.values.get('messages', [])
    except Exception as e:
        st.error(f"⚠️ Failed to load conversation for thread {thread_id}: {e}")
        return []


########################## Session Setup #################################

# Initialize message history if not already present
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

# Generate a new thread ID if not already stored
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

# Retrieve all existing thread IDs from backend and store in session state
if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

# Make sure the current thread_id is added to chat_threads
add_thread(st.session_state['thread_id'])

# >>> Added for Suggestion 2: Thread Naming
# Dictionary to store human-readable thread names for display
if 'thread_names' not in st.session_state:
    st.session_state['thread_names'] = {}

def get_thread_display_name(thread_id):
    """
    Get the display name for a thread.
    If the user renamed it, show the custom name.
    Otherwise, show a shortened UUID.
    """
    return st.session_state['thread_names'].get(thread_id, str(thread_id)[:8])


#************************************************* Sidebar UI **********************************************************

st.sidebar.title('Langgraph Chatbot')

# Button to start a new chat session
if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My conversations')

# >>> Added for Suggestion 4: Use expander for better organization
with st.sidebar.expander("Conversation Threads", expanded=True):
    for thread_id in st.session_state['chat_threads'][::-1]:
        # Show thread display name instead of raw UUID
        if st.sidebar.button(get_thread_display_name(thread_id)):
            # Switch to selected thread
            st.session_state['thread_id'] = thread_id

            # Load messages for that thread
            messages = load_conversation(thread_id)

            temp_messages = []
            for msg in messages:
                # Identify role based on message type
                if isinstance(msg, HumanMessage):
                    role = 'user'
                else:
                    role = 'assistant'
                temp_messages.append({'role': role, 'content': msg.content})

            # Update session message history with the loaded conversation
            st.session_state['message_history'] = temp_messages

    # Allow user to rename current thread for readability
    current_thread_id = st.session_state['thread_id']
    new_name = st.text_input(
        "Rename current thread:",
        value=st.session_state['thread_names'].get(current_thread_id, ""),
        placeholder="Enter custom name..."
    )
    if new_name:
        st.session_state['thread_names'][current_thread_id] = new_name


#************************************************** Main UI *************************************************************

# Display the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

# Input box for user to type messages
user_input = st.chat_input('Type Here')

if user_input:
    # 1. Add user message to session history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    # 2. Prepare configuration for chatbot (thread-specific)
    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    # 3. Stream assistant’s response
    with st.chat_message('assistant'):
        # >>> Added for Suggestion 1: Error Handling
        try:
            ai_message = st.write_stream(
                message_chunk.content for message_chunk, metadata in chatbot.stream(
                    {'messages': [HumanMessage(content=user_input)]},  # initial state
                    config=CONFIG,  # pass thread config
                    stream_mode='messages'  # stream token by token as messages
                )
            )
        except Exception as e:
            st.error(f"⚠️ Failed to get response from chatbot: {e}")
            ai_message = "Sorry, something went wrong."

    # 4. Add assistant response to session history
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
