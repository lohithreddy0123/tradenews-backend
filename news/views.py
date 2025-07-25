import os
import re
import requests
from django.http import JsonResponse
from dotenv import load_dotenv

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def get_news_for_stock(request, stock_name=None):
    if not NEWS_API_KEY:
        return JsonResponse({"error": "Missing News API key."}, status=500)

    # Support optional query param `keywords=bitcoin,crypto`
    raw_keywords = request.GET.get("keywords")
    limit = request.GET.get("limit", 5)

    try:
        limit = int(limit)
    except ValueError:
        limit = 5

    if raw_keywords:
        keywords = [k.strip() for k in raw_keywords.split(",") if k.strip()]
    elif stock_name:
        # Fallback to URL path param
        clean_name = re.sub(r"\(.*?\)", "", stock_name).strip()
        keywords = [clean_name]
    else:
        return JsonResponse({"error": "No stock name or keywords provided."}, status=400)

    query = " OR ".join(
    [f'"{word}"' if " " in word else word for word in keywords]
)

    print(f"🌐 Fetching news for: {keywords} → Query: {query} | Limit={limit}")

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": limit,
        "apiKey": NEWS_API_KEY,
    }

    response = requests.get(url, params=params)
    print(f"📡 News API status code: {response.status_code}")

    try:
        data = response.json()
        print("📰 Raw response snippet:", str(data)[:300])

        if response.status_code == 200 and data.get("status") == "ok":
            articles = [
                {
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "source": article.get("source", {}).get("name"),
                    "url": article.get("url"),
                    "publishedAt": article.get("publishedAt"),
                }
                for article in data.get("articles", [])
            ]

            if not articles:
                print(f"ℹ️ No articles found for query: {query}")

            return JsonResponse({"articles": articles})
        else:
            print("⚠️ NewsAPI error message:", data.get("message", "Unknown error"))
            return JsonResponse(
                {"error": data.get("message", "Failed to fetch news")},
                status=response.status_code,
            )

    except Exception as e:
        print("❌ Error parsing NewsAPI response:", str(e))
        return JsonResponse({"error": "Internal server error"}, status=500)
