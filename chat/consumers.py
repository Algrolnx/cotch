import json
import uuid
import re
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .agent import app
from .tools import get_todays_tasks
from langchain_core.messages import HumanMessage

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = "main_coach_thread_1"
        await self.accept()

        try:
            tasks_str = await sync_to_async(get_todays_tasks.invoke)({})
        except Exception as e:
            tasks_str = f"Не вдалося отримати задачі: {e}"

        import datetime
        from zoneinfo import ZoneInfo
        ukraine_tz = ZoneInfo("Europe/Kyiv")
        current_time_str = datetime.datetime.now(ukraine_tz).strftime("%H:%M")

        init_message = f"""
        Я щойно відкрив додаток. Ось мій поточний місцевий час: {current_time_str}.
        Ось мої задачі на сьогодні з Todoist (я вже отримав їх для тебе, не викликай інструмент!):
        {tasks_str}

        Вказівки:
        - Якщо зараз РАНОК (06:00-11:59): зроби бадьорий ранковий чекін + план на день, розбираючи ці задачі.
        - Якщо зараз ДЕНЬ (12:00-17:59): запитай, як проходить мій день та чим допомогти з цими задачами.
        - Якщо зараз ВЕЧІР (18:00-23:59): зроби вечірній підсумок: спитай, що вдалося зробити з цього списку і як мій настрій.
        
        Зроби це природно, як жива людина! Не кажи "ось задачі, які ти мені передав", просто вплітай їх у свою розмову як факт.
        """
        
        try:
            response_message = await sync_to_async(self.invoke_agent)(init_message)
            await self.send(text_data=json.dumps({
                'message': response_message
            }))
        except Exception as e:
            print(f"Помилка при першому чекіні: {str(e)}")

    async def disconnect(self, close_code):
        pass

    def invoke_agent(self, msg_text):
        inputs = {"messages": [HumanMessage(content=msg_text)]}
        config = {"configurable": {"thread_id": self.thread_id}}
        result = app.invoke(inputs, config=config)
        
        raw_content = result["messages"][-1].content
        clean_content = re.sub(r'<function.*?>.*?</function>', '', raw_content, flags=re.DOTALL)
        return clean_content.strip()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        if message.strip().lower() == "/clear" or message.strip().lower() == "забудь все":
            self.thread_id = str(uuid.uuid4())
            await self.send(text_data=json.dumps({
                'message': "Пам'ять успішно очищено! Починаємо з чистого аркуша."
            }))
            return

        try:
            response_message = await sync_to_async(self.invoke_agent)(message)
        except Exception as e:
            response_message = f"Error: {str(e)}"

        await self.send(text_data=json.dumps({
            'message': response_message
        }))
