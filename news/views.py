import os
import re
import requests
from django.http import JsonResponse
from dotenv import load_dotenv

load_dotenv()
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

def get_news_for_stock(request, stock_name=None):
    if not FINNHUB_API_KEY:
        return JsonResponse({"error": "Missing Finnhub API key."}, status=500)

    # Extract GET parameters
    raw_keywords = request.GET.get("keywords")
    symbol_param = request.GET.get("symbol", "").strip().upper()
    limit = request.GET.get("limit", 5)

    try:
        limit = int(limit)
    except ValueError:
        limit = 5

    # Prepare keywords if any
    if raw_keywords:
        keywords = [k.strip() for k in raw_keywords.split(",") if k.strip()]
    elif stock_name:
        clean_name = re.sub(r"\(.*?\)", "", stock_name).strip()
        keywords = [clean_name]
    else:
        keywords = []

    # ✅ Determine symbol: prioritize explicit `symbol`, fallback to name-based
    if symbol_param:
        symbol = symbol_param
    elif stock_name:
        symbol = re.sub(r"\(.*?\)", "", stock_name).strip().upper()
    elif keywords:
        symbol = keywords[0].upper()
    else:
        return JsonResponse({"error": "No symbol or keywords provided."}, status=400)

    print(f"🌐 [Finnhub] Fetching news for: {symbol}")

    from datetime import datetime, timedelta
    to_date = datetime.utcnow().date().isoformat()
    from_date = (datetime.utcnow() - timedelta(days=5)).date().isoformat()

    url = "https://finnhub.io/api/v1/company-news"
    params = {
        "symbol": symbol,
        "from": from_date,
        "to": to_date,
        "token": FINNHUB_API_KEY,
    }

    response = requests.get(url, params=params)
    print(f"📡 Finnhub API status code: {response.status_code}")

    try:
        data = response.json()
        print("📰 Raw response snippet:", str(data)[:300])

        if isinstance(data, list) and data:
            articles = [
                {
                    "title": a.get("headline"),
                    "description": a.get("summary"),
                    "source": a.get("source"),
                    "url": a.get("url"),
                    "publishedAt": a.get("datetime"),
                }
                for a in data[:limit]
            ]
            return JsonResponse({"articles": articles})
        else:
            return JsonResponse({"articles": []})
    except Exception as e:
        print("❌ Error parsing Finnhub response:", str(e))
        return JsonResponse({"error": "Internal server error"}, status=500)
