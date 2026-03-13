import os
import sqlite3
import operator
from typing import TypedDict, Annotated
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode, tools_condition

from .tools import get_todays_tasks

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, '.env'), override=True)

llm = ChatGroq(
    model='llama-3.3-70b-versatile',
    api_key=os.getenv('GROQ_API_KEY'),
    temperature=0.1
)

tools = [get_todays_tasks]
llm_with_tools = llm.bind_tools(tools)

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]

def chatbot_node(state: AgentState):
    messages = state['messages']
    
    if not any(isinstance(m, SystemMessage) for m in messages):
        system_prompt = SystemMessage(content="""
        Ти - професійний AI-коуч. Ти розмовляєш українською мовою.
        
        ПРАВИЛО 1: Якщо користувач питає про плани на сьогодні, розклад або що робити - ТИ ПОВИНЕН використати інструмент 'get_todays_tasks'.
        ПРАВИЛО 2: Ти вже маєш необхідні ключі API. Не кажи користувачу про авторизацію чи налаштування! Просто бери інформацію з інструменту і віддавай її у красивому вигляді.
        """)
        messages = [system_prompt] + messages
    
    response = llm_with_tools.invoke(messages)
    return {'messages': [response]}

workflow = StateGraph(AgentState)
workflow.add_node('chatbot', chatbot_node)
workflow.add_node('tools', ToolNode(tools)) 

workflow.set_entry_point('chatbot')

workflow.add_conditional_edges("chatbot", tools_condition)
workflow.add_edge("tools", "chatbot")

conn = sqlite3.connect('db.sqlite3', check_same_thread=False)
memory = SqliteSaver(conn)
app = workflow.compile(checkpointer=memory)
