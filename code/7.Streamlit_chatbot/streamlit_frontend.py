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
    
    response = chatbot.invoke({'messages':[HumanMessage(content=user_input)]}, config=CONFIG) # LLMs response to user_query
    ai_message = response['messages'][-1].content

    # first add the message to message_history
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
    with st.chat_message('assistant'):
        st.text(ai_message)