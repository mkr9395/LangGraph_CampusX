from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3 # to create sql databases

load_dotenv()


llm = ChatOpenAI()

class ChatState(TypedDict):
    messages : Annotated[list[BaseMessage], add_messages]
    
    
def chat_node(state : ChatState) :
    messages = state['messages']
    response = llm.invoke(messages)
    return {'messages' : [response]}

# create sql database
conn = sqlite3.connect(database= 'chatbot.db', check_same_thread=False) # create new database chatbot.db in project directory

# checkpointer
checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)

# node
graph.add_node('chat_node', chat_node) 

# edges
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)   

# using the checkpointer
chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_threads = set() # to get names of all unique threads
    # extract number of checkpoint for each threads already present in the database
    for checkpoint in checkpointer.list(None) : # by None we will get all the checkpoint of all the thread ids
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    
    
    return list(all_threads)

