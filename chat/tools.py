import os
import datetime
from dotenv import load_dotenv
from langchain_core.tools import tool
from todoist_api_python.api import TodoistAPI

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=ENV_PATH, override=True)

@tool
def get_todays_tasks() -> str:
    """
    Отримує список завдань на сьогодні з Todoist. 
    Викликай цей інструмент ЗАВЖДИ, коли користувач питає про плани на сьогодні, задачі або що йому робити.
    """
    token = os.getenv("TODOIST_API_KEY")
    if not token:
        return f"Can't get tasks from Todoist: API key not found. Checked file: {ENV_PATH}"
    
    api = TodoistAPI(token)
    try:
        all_tasks = []
        for batch in api.get_tasks():
            if isinstance(batch, list):
                all_tasks.extend(batch)
            else:
                all_tasks.append(batch)
        
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        tasks = []
        for t in all_tasks:
            due = getattr(t, "due", None)
            if due:
                due_date = str(getattr(due, "date", ""))
                if due_date == today_str:
                    tasks.append(t)
        
        if not tasks:
            return "На сьогодні завдань у Todoist не знайдено. Ти вільний!"
        
        result = "Твої задачі на сьогодні:\n"
        for i, task in enumerate(tasks, start=1):
            result += f"{i}. {task.content}\n"
        return result
    except Exception as e:
        return f"Can't get tasks from Todoist: {str(e)}"


@tool 
def add_todoist_task(content: str) -> str:
    """
    Додає нове завдання в Todoist на сьогодні.
    Викликай цей інструмент, коли користувач просить 'додай задачу', 'нагадай мені', або щось подібне.
    Аргумент content - це текст самої задачі (наприклад, 'Купити молоко').
    """
    token = os.getenv('TODOIST_API_KEY')
    api = TodoistAPI(token)
    try:
        api.add_task(content=content, due_string='today')
        return f"Завдання '{content}' додано до Todoist на сьогодні."
    except Exception as e:
        return f"Can't add task to Todoist: {str(e)}"

@tool
def complete_todoist_task(task_text: str) -> str:
    """
    Позначає існуюче завдання в Todoist як виконане (закриває його).
    Викликай цей інструмент, коли користувач каже 'я виконав задачу X', 'закрий задачу X' або 'видали X'.
    Аргумент task_text - це назва задачі або її частина, яку треба закрити.
    """
    token = os.getenv('TODOIST_API_KEY')
    api = TodoistAPI(token)
    try:
        all_tasks = []
        for batch in api.get_tasks():
            if isinstance(batch, list):
                all_tasks.extend(batch)
            else:
                all_tasks.append(batch)

        target_task = None
        for t in all_tasks:
            if task_text.lower() in t.content.lower():
                target_task = t 
                break
        
        if not target_task:
            return f"Не знайдено завдання '{task_text}' в Todoist."

        is_success = api.delete_task(task_id=target_task.id)
        if is_success:
            return f"Завдання '{target_task.content}' успішно видалено."
        else:
            return f"Завдання '{target_task.content}' видалено (або вже не існувало)."

    except Exception as e:
        return f"Can't close task in Todoist: {str(e)}"