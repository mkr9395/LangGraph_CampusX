import streamlit as st
from langgrapgh_backend import chatbot
from langchain_core.messages import HumanMessage

import uuid # to create random new threads

#************************************************* Utility functions**********************************

# utility functions to create random thread
def generate_thread_id():
    """
    will give random new thread
    """
    thread_id = uuid.uuid4()
    
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id # store the new thread id for new conversation
    add_thread(st.session_state['thread_id']) # add the new thread to chat
    st.session_state['message_history'] = [] # emptying the message history
    
def add_thread(thread_id):
    """
    if the new thread is not present in chat_threads then add it to the list.
    """
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)
        


def load_conversation(thread_id):
    """
    when the function is given a thread_id it will return the entire message list store in it
    """
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    # Check if messages key exists in state values, return empty list if not
    return state.values.get('messages', [])



########################## Session Setup #################################


if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
    
# add new thread id to session state    
if 'thread_id' not in st.session_state: # if thread id is not set
    st.session_state['thread_id'] = generate_thread_id()
    
if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []    
    
add_thread(st.session_state['thread_id'])
    

#************************************************* Sidebar UI **********************************************************

st.sidebar.title('Langgraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat() # if new_chat button is clicked then reset the chat

st.sidebar.header('My conversations')

# display all thread_ids in the sidebar
for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(str(thread_id)): # if the new chat button is clicked then do the below work
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id) # load the messages from the current thread id
        
        temp_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage): # if instance of current message is HumanMessage the rol ='user' else 'assistant'
                role='user'
            else:
                role='assistant'
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_messages

#************************************************** Main UI *************************************************************

# loading the conversation history
# display all messages inside the message_history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']): # for each message in message history, load its role and then content 
        st.text(message['content'])


user_input = st.chat_input('Type Here')

        
if user_input: # for new user message
    
    # first add message to message_history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)
        
    # st.session_state -> dict ->
    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}} # add thread_id here
    
    # first add the message to message_history
    
    with st.chat_message('assistant'):
        
        ai_message = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot.stream(
            {'messages':[HumanMessage(content=user_input)]}, # 1. initial state
            config = CONFIG, # 2. add the config
            stream_mode = 'messages' # 3. stream_mode -> message -> token by token
            ))
            
            # if message_chunk.content:
            #     print(message_chunk.content, end = " ", flush = True)
            
            
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
                

