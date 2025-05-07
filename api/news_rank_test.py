from datasets import load_dataset
from datetime import datetime, timedelta
import random
import json
from datetime import timezone

dataset = load_dataset("ag_news", split="train")
articles = []

for i, item in enumerate(dataset.select(range(200))):  # Limit for testing
    articles.append({
        "id": str(i),
        "title": item["text"],
        "body": item["text"],
        "source_score": round(random.uniform(0.5, 1.0), 2),
        "published_at": (datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 48))).isoformat(),
        "clicks": random.randint(0, 200),
        "shares": random.randint(0, 50)
    })

with open("rank_input.json", "w", encoding="utf-8") as f:
    json.dump(articles, f, indent=2, ensure_ascii=False)

import requests
import json

# Load the JSON data
with open("rank_input.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Send POST request to your local FastAPI server
res = requests.post("http://localhost:8001/v1/rank", json=data)

# Show the results
print("Status Code:", res.status_code)
print("Top 5 Ranked Articles:")
for item in res.json()[:5]:
    print(item)

# Print top article details
top_ids = [item['id'] for item in res.json()[:5]]
print("\n--- Top Article Details ---")
for art in data:
    if art["id"] in top_ids:
        print(f"ID: {art['id']}, Score: {[i['score'] for i in res.json() if i['id'] == art['id']][0]}")
        print(f"Title: {art['title']}")
        print(f"Clicks: {art['clicks']}, Shares: {art['shares']}")
        print(f"Published: {art['published_at']}, Source: {art['source_score']}")
        print("-" * 60)
