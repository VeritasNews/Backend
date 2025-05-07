# api/utils/news_ranker.py
import requests

FASTAPI_RANKING_URL = "https://ranker-service.onrender.com/v1/rank"

def rank_articles(articles, genre="politics", country="TR"):
    payload = [
        {
            "id": str(a.articleId),
            "title": a.title or "",
            "body": a.longerSummary or a.summary or "",
            "source_score": 0.8,
            "published_at": a.createdAt.isoformat() if a.createdAt else "2025-01-01T00:00:00Z",
            "clicks": a.popularityScore or 0,
            "shares": getattr(a, "liked_count", 0),
        }
        for a in articles
    ]

    try:
        response = requests.post(FASTAPI_RANKING_URL, json=payload, params={"genre": genre, "country": country})
        if response.status_code == 200:
            return response.json()
        else:
            print("⚠️ Failed to get ranking:", response.text)
            return []
    except Exception as e:
        print("❌ Ranking service error:", e)
        return []
