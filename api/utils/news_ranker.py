# api/utils/news_ranker.py
import requests

FASTAPI_RANKING_URL = "http://144.91.84.230:8002/v1/rank"  # Updated with your backend server

def rank_articles(articles, genre="siyaset", country="TR"):
    payload = []
    for a in articles:
        try:
            published_at = a.createdAt.isoformat() if hasattr(a.createdAt, "isoformat") else str(a.createdAt)
            payload.append({
                "id": str(a.articleId),
                "title": a.title or "",
                "body": a.longerSummary or a.summary or "",
                "source_score": 0.8,
                "published_at": published_at,
                "clicks": a.popularityScore or 0,
                "shares": getattr(a, "liked_by_users", []).count() if hasattr(a, "liked_by_users") else 0,
            })
        except Exception as e:
            print("❌ Error preparing article:", a, str(e))

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
