import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NewsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # Optionally send initial message on connection
        await self.send(json.dumps({
            'headline': '🔍 Connected to news feed',
            'summary': 'Waiting for backend news updates...',
            'sentiment': 'neutral',
        }))

    async def disconnect(self, close_code):
        # Clean up if needed
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        stock = data.get('stock')

        # Here, you would trigger your backend logic to analyze news
        # For demo, send back a static news block

        news_data = {
            'headline': f'Live news update for {stock}',
            'impact': 'High',
            'direction': 'Upside',
            'summary': 'This is a sample live news update from backend.',
            'sentiment': 'positive',
            'source': 'Backend',
            'time': '2025-07-25T12:00:00Z',
        }

        await self.send(json.dumps(news_data))
