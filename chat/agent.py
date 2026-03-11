import os
import sqlite3
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict, Annotated
import operator

load_dotenv()

llm = ChatGroq(
    model='llama-3.3-70b-versatile',
    api_key=os.getenv('GROQ_API_KEY')
)

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]

def chatbot_node(state: AgentState):
    messages = state['messages']

    if not messages or not isinstance(messages[0], SystemMessage):
        system_prompt = SystemMessage(content="""
        Ти - персональний AI-коуч. Твоя мета - підтримувати користувача, допомагати досягати цілей. 
        Пиши коротко, чітко, українською мовою. Став запитання, щоб зрозуміти контекст дня.
        """)
        messages = [system_prompt] + messages

    response = llm.invoke(messages)
    return {'messages': [response]}

workflow = StateGraph(AgentState)
workflow.add_node('chatbot', chatbot_node)
workflow.set_entry_point('chatbot')
workflow.add_edge('chatbot', END)

conn = sqlite3.connect('db.sqlite3', check_same_thread=False)
memory = SqliteSaver(conn)
app = workflow.compile(checkpointer=memory)

