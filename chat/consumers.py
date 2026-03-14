import json
import uuid
import re
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .agent import app
from langchain_core.messages import HumanMessage

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = "main_coach_thread_1"
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        if message.strip().lower() == "/clear" or message.strip().lower() == "забудь все":
            self.thread_id = str(uuid.uuid4())
            await self.send(text_data=json.dumps({
                'message': "Пам'ять успішно очищено! Починаємо з чистого аркуша."
            }))
            return
        
        def invoke_agent():
            inputs = {"messages": [HumanMessage(content=message)]}
            config = {"configurable": {"thread_id": self.thread_id}}
            result = app.invoke(inputs, config=config)
            
            raw_content = result["messages"][-1].content
            clean_content = re.sub(r'<function.*?>.*?</function>', '', raw_content, flags=re.DOTALL)
            return clean_content.strip()
        
        try:
            response_message = await sync_to_async(invoke_agent)()
        except Exception as e:
            response_message = f"Error: {str(e)}"

        await self.send(text_data=json.dumps({
            'message': response_message
        }))
