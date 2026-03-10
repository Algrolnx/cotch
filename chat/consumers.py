import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        response_message = f"Я почув тебе. Ти сказав: '{message}'"

        await self.send(text_data=json.dumps({
            'message': response_message
        }))
