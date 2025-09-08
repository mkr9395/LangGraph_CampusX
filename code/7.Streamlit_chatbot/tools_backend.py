from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3 # to create sql databases
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
import requests
import os

load_dotenv()

# -------------------
# 1. LLM
# -------------------
llm = ChatOpenAI()

# -------------------
# 2. Tools
# -------------------
# Tools

search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def calculator(first_num : float, second_num : float, operation : str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {'error':'Divsion by zero is not allowed'}
            result = first_num/second_num
        else:
            return {"error" : f"Unsupported operation {operation}"}
        
        return {"first_num" : first_num, "second_num" : second_num , "opeartion":operation, "result":result}
    
    except exception as e:
        return {"error" : str(e)}
    
    
alpha_vantage = os.getenv("ALPHAVANTAGE_API_KEY")

@tool    
def get_stock_price(symbol : str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={alpha_vantage}"
    
    r = requests.get(url)
    return r.json()

tools = [search_tool, get_stock_price, calculator]
llm_with_tools = llm.bind_tools(tools)
            
            
# -------------------
# 3. State
# -------------------   
    
class ChatState(TypedDict):
    messages : Annotated[list[BaseMessage], add_messages]
    
# -------------------
# 4. Nodes
# -------------------
def chat_node(state: ChatState):
    """LLM node that may answer or request a tool call."""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}    

tool_node = ToolNode(tools)


# -------------------
# 5. Checkpointer
# -------------------
   
    
# create sql database
conn = sqlite3.connect(database= 'chatbot.db', check_same_thread=False) # create new database chatbot.db in project directory

# checkpointer
checkpointer = SqliteSaver(conn=conn)


# -------------------
# 6. Graph
# -------------------

graph = StateGraph(ChatState)

# node
graph.add_node('chat_node', chat_node) 
graph.add_node('tools', tool_node)

# edges
graph.add_edge(START, 'chat_node')

graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools','chat_node')

# using the checkpointer
chatbot = graph.compile(checkpointer=checkpointer)


# -------------------
# 7. Helper
# -------------------

def retrieve_all_threads():
    all_threads = set() # to get names of all unique threads
    # extract number of checkpoint for each threads already present in the database
    for checkpoint in checkpointer.list(None) : # by None we will get all the checkpoint of all the thread ids
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    
    return list(all_threads)

