import os
import sqlite3
import operator
import datetime
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

from langchain_cohere import ChatCohere
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode, tools_condition


from .tools import get_todays_tasks, add_todoist_task, complete_todoist_task

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, '.env'), override=True)

llm = ChatCohere(
    model='command-r-08-2024',
    cohere_api_key=os.getenv('COHERE_API_KEY'),
    max_tokens=1200,
    temperature=0.1
)

tools = [get_todays_tasks, add_todoist_task, complete_todoist_task]
llm_with_tools = llm.bind_tools(tools)

class AgentState(TypedDict):
    messages: Annotated[list, operator.add] 

def chatbot_node(state: AgentState):
    messages = state['messages']
    
    ukraine_tz = ZoneInfo("Europe/Kyiv")
    current_time = datetime.datetime.now(ukraine_tz).strftime("%H:%M, %d %B %Y")
    
    system_prompt = SystemMessage(content=f"""
    Ти - професійний AI-коуч. Ти розмовляєш українською мовою.
    Поточна дата і час: {current_time}. Зважай на це (ранок, день чи вечір) при спілкуванні і плануванні!
    
    Твій арсенал інструментів для Todoist:
    1. 'get_todays_tasks' - викликай ЗАВЖДИ, коли питають про плани на сьогодні.
    2. 'add_todoist_task' - викликай, коли просять "додай", "запиши", "нагадай" зробити щось.
    3. 'complete_todoist_task' - викликай, коли кажуть "я зробив", "закрий задачу", "видали".
    
    ВАЖЛИВО: НІКОЛИ не виводь теги функцій (напр. <function=...>) у текстовій відповіді! Використовуй інструменти приховано. Просто відповідай як людина-коуч.
    """)
    
    filtered_messages = [m for m in messages if not isinstance(m, SystemMessage)]
    messages = [system_prompt] + filtered_messages
    
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
