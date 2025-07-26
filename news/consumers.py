import json
import os
import aiohttp
from datetime import datetime, timedelta
from channels.generic.websocket import AsyncWebsocketConsumer
import openai
from dotenv import load_dotenv

load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY


class NewsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("✅ [WebSocket] Connection established.")

    async def disconnect(self, code):
        print(f"🔌 [WebSocket] Disconnected with code: {code}")

    async def receive(self, text_data):
        print("📨 [Frontend] Data received:", text_data)

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(json.dumps({"error": "Invalid JSON format"}))
            return

        if data.get("action") == "start":
            keywords = data.get("keywords")
            symbol = data.get("symbol", "").strip().upper()

            print(f"📦 Keywords received: {keywords}")
            print(f"🏷️ Symbol received: {symbol}")

            if not symbol:
                await self.send(json.dumps({"error": "Missing or invalid symbol"}))
                return

            if not keywords or not isinstance(keywords, list):
                await self.send(json.dumps({"error": "No valid keywords provided"}))
                return

            article_text = await self.fetch_news(symbol)

            if not article_text:
                await self.send(json.dumps({
                    "headline": f"⚠️ No News Found for {' / '.join(keywords)}",
                    "summary": "Try another stock or wait for updates.",
                    "impact": "Low",
                    "direction": "Sideways",
                    "sentiment": "neutral",
                    "time": datetime.utcnow().isoformat(),
                    "source": "Finnhub",
                    "traderAdvice": "No action recommended.",
                }))
                return

            ai_response = await self.analyze_with_openai(article_text, ', '.join(keywords))
            await self.send(text_data=json.dumps(ai_response))

    async def fetch_news(self, symbol):
        from_date = (datetime.utcnow() - timedelta(days=5)).date().isoformat()
        to_date = datetime.utcnow().date().isoformat()

        url = (
            f"https://finnhub.io/api/v1/company-news"
            f"?symbol={symbol}&from={from_date}&to={to_date}&token={FINNHUB_API_KEY}"
        )

        print(f"🌐 Finnhub Request URL:\n{url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                print(f"📡 Finnhub API status: {response.status}")
                try:
                    data = await response.json()
                    print("📰 Full Finnhub News Response (first 8 shown):\n", json.dumps(data[:8], indent=2))
                except Exception as e:
                    print("❌ Failed to parse response:", e)
                    return None

                if isinstance(data, list) and len(data):
                    articles = data[:6]  # ✅ Take first 6 articles for processing

                    trimmed = ""
                    for i, article in enumerate(articles, start=1):
                        headline = article.get("headline", "")
                        summary = article.get("summary", "")
                        trimmed += f"Article {i}:\nHeadline: {headline}\nSummary: {summary}\n\n"

                    print("🧾 Trimmed multi-article block:\n", trimmed[:500])
                    return trimmed[:3000]  # safe size limit

        return None

    async def analyze_with_openai(self, article_text, topic_label):
        prompt = f"""
You're a financial news analyst.

Given this news related to "{topic_label}", analyze and return structured output in JSON:

{{
  "headline": "...",
  "summary": "...",
  "impact": "...",  // High, Medium, Low
  "direction": "...",  // Up, Down, Sideways
  "sentiment": "...",  // positive, negative, neutral
  "time": "...",  // ISO timestamp
  "source": "Finnhub",
  "traderAdvice": "..."
}}

News:
\"\"\"
{article_text}
\"\"\"
"""

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=400,
            )
            reply = response["choices"][0]["message"]["content"]
            print("📥 OpenAI Reply Preview:", reply[:400])
            return json.loads(reply)
        except Exception as e:
            print("❌ OpenAI Analysis error:", e)
            return {
                "headline": "⚠️ Analysis Failed",
                "summary": "Could not analyze news.",
                "impact": "Low",
                "direction": "Sideways",
                "sentiment": "neutral",
                "time": datetime.utcnow().isoformat(),
                "source": "System",
                "traderAdvice": "Please retry later.",
            }
