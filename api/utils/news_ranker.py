import requests

FASTAPI_RANKING_URL = "http://144.91.84.230:8002/rank"  # Updated with your backend server

def rank_articles(articles, genre="siyaset", country="TR"):
    # Transform the data to match the FastAPI expected format
    payload = {
        "articles": [],
        "debug": False  # Set to True if you want detailed scoring breakdown
    }
    
    for a in articles:
        try:
            published_at = a.createdAt.isoformat() if hasattr(a.createdAt, "isoformat") else str(a.createdAt)
            
            # Map your article data to the format expected by the FastAPI endpoint
            article_data = {
                "title": a.title or "",
                "content": a.longerSummary or a.summary or "",  # Content field in the API
                "timestamp": published_at,  # ISO format timestamp
                "source": getattr(a, "source", "default_source"),  # Add source if available
                "views": a.popularityScore or 0,
                "likes": getattr(a, "liked_by_users", []).count() if hasattr(a, "liked_by_users") else 0,
                "comments": 0  # If you have comments data, add it here
            }
            
            payload["articles"].append(article_data)
        except Exception as e:
            print("❌ Error preparing article:", a, str(e))

    if not payload["articles"]:
        print("⚠️ No valid articles to rank")
        return []

    try:
        # Pass the genre and country as query parameters
        response = requests.post(
            FASTAPI_RANKING_URL, 
            json=payload, 
            params={"genre": genre, "country": country},
            timeout=5  # Add a timeout to prevent hanging
        )
        
        if response.status_code == 200:
            ranked_data = response.json()
            # Map returned data back to your expected format if needed
            return [
                {
                    "id": item["article"].get("id", ""),  # Adjust this mapping as needed
                    "score": item["score"]
                } 
                for item in ranked_data
            ]
        else:
            print(f"⚠️ Failed to get ranking: Status {response.status_code}")
            print(f"Response: {response.text}")
            return []
    except Exception as e:
        print("❌ Ranking service error:", e)
        return []