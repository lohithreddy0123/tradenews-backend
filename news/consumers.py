import json
import os
import aiohttp
from datetime import datetime, timedelta
from channels.generic.websocket import AsyncWebsocketConsumer
import openai

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
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
        except json.JSONDecodeError as e:
            print("❌ [JSON] Decode error:", e)
            await self.send(json.dumps({"error": "Invalid JSON format"}))
            return

        if data.get("action") == "start":
            keywords = data.get("keywords")
            print(f"📦 [Frontend] Keywords received: {keywords}")

            if not keywords or not isinstance(keywords, list):
                await self.send(json.dumps({"error": "No valid keywords provided"}))
                return

            # Properly quote keywords with spaces
            query_terms = [
                f'"{kw}"' if " " in kw else kw for kw in keywords
            ]
            query = " OR ".join(query_terms)
            print(f"🔍 [NewsAPI] Constructed query: {query}")

            article_text = await self.fetch_news(query)

            if not article_text:
                print("⚠️ [NewsAPI] No articles found.")
                await self.send(json.dumps({
                    "headline": f"⚠️ No News Found for {' / '.join(keywords)}",
                    "summary": "Try another stock or wait for updates.",
                    "impact": "Low",
                    "direction": "Sideways",
                    "sentiment": "neutral",
                    "time": datetime.utcnow().isoformat(),
                    "source": "News API",
                    "traderAdvice": "No action recommended.",
                }))
                return

            print("📰 [NewsAPI] Article fetched, sending to OpenAI...")
            ai_response = await self.analyze_with_openai(article_text, ', '.join(keywords))
            print("✅ [OpenAI] Response received.")

            await self.send(text_data=json.dumps(ai_response))

    async def fetch_news(self, query):
        from_date = (datetime.utcnow() - timedelta(days=3)).date().isoformat()
        url = (
            f"https://newsapi.org/v2/everything"
            f"?q={query}&from={from_date}&sortBy=popularity&pageSize=1&language=en"
            f"&apiKey={NEWS_API_KEY}"
        )

        print(f"🌐 [NewsAPI] Request URL:\n{url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                print(f"📡 [NewsAPI] Status code: {response.status}")

                try:
                    data = await response.json()
                except Exception as e:
                    print("❌ [NewsAPI] Failed to parse response:", e)
                    return None

                print("🧾 [NewsAPI] Response preview:", json.dumps(data, indent=2)[:800])

                if data.get("status") == "ok" and data.get("articles"):
                    article = data["articles"][0]
                    title = article.get("title", "")
                    desc = article.get("description", "")
                    trimmed = f"{title}\n\n{desc}".strip()
                    print("✂️ [NewsAPI] Trimmed article preview:", trimmed[:300], "...")
                    return trimmed[:1500]

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
  "source": "News API",
  "traderAdvice": "..."
}}

News:
\"\"\" 
{article_text}
\"\"\"
"""
        print("🧠 [OpenAI] Sending prompt...")

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=400,
            )

            reply = response["choices"][0]["message"]["content"]
            print("📥 [OpenAI] Raw reply preview:", reply[:400])
            return json.loads(reply)

        except Exception as e:
            print("❌ [OpenAI] Analysis error:", e)
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
