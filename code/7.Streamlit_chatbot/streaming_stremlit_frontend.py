import streamlit as st
from langgrapgh_backend import chatbot
from langchain_core.messages import HumanMessage


# st.session_state -> dict ->
CONFIG = {'configurable': {'thread_id': 'thread-1'}}

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []



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
    
    # first add the message to message_history
    
    with st.chat_message('assistant'):
        
        ai_message = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot.stream(
            {'messages':[HumanMessage(content=user_input)]}, # 1. initial state
            config = {'configurable': {'thread_id': 'thread-1'}}, # 2. add the config
            stream_mode = 'messages' # 3. stream_mode -> message -> token by token
            ))
            
            # if message_chunk.content:
            #     print(message_chunk.content, end = " ", flush = True)
            
            
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
                