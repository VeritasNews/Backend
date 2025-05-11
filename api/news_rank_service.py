from fastapi import FastAPI, Query
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Union
import requests
import re
import logging
from functools import lru_cache

# --- App Metadata ---
app = FastAPI(
    title="News Ranking API",
    description="Ranks news articles based on multiple features like recency, source, engagement, etc.",
    version="1.0.0"
)

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Constants ---
TR_LOCATIONS = {
    "istanbul", "ankara", "izmir", "bursa", "antalya", "adana", "konya",
    "trabzon", "gaziantep", "diyarbakır", "kayseri", "mersin", "van",
    "karabük", "kocaeli", "sakarya", "manisa", "edirne", "rize", "ordu",
}

HOT_TOPICS = {
    "deprem", "ekonomi", "siyaset", "enflasyon", "zam",
    "seçim", "aselsan", "savunma", "yapay zeka", "göçmen", "terör",
    "iran", "israil", "ukrayna", "abd", "cumhurbaşkanı", "imamoğlu", "erdoğan", "ekrem imamoğlu", 
    "özgür özel", "chp", "akp", "mhp", "dem", "gezi", "kılıçdaroğlu", 
}

SOURCE_WEIGHTS = {
    "hurriyet": 1.0,
    "cnn": 1.0,
    "ntv": 1.0,
    "sozcu": 1.3,
    "haberler": 1.1,
    "milliyet": 1.0,
    "ensonhaber": 0.9,
    "tele1": 1.3,
    "t24": 1.0,
    "bianet": 1.2,
    "cumhuriyet": 1.3,
    "ahaber": -0.5,
}

SCORE_WEIGHTS = {
    "source": 0.18,
    "recency": 0.20,
    "engagement": 0.20,
    "geo": 0.17,
    "severity": 0.15,
    "trend": 0.10,
}

# --- Models ---
class NewsArticle(BaseModel):
    title: str
    content: str
    timestamp: str
    source: str
    views: int = Field(0, ge=0)
    likes: int = Field(0, ge=0)
    comments: int = Field(0, ge=0)

    @validator("timestamp")
    def validate_timestamp(cls, value):
        try:
            datetime.fromisoformat(value)
        except ValueError:
            raise ValueError("timestamp must be ISO format (YYYY-MM-DDTHH:MM:SS)")
        return value

class NewsRankRequest(BaseModel):
    articles: List[NewsArticle]
    debug: bool = False

class NewsRankedResponse(BaseModel):
    article: NewsArticle
    score: float
    details: Union[dict, None] = None

# --- Utility Functions ---
def normalize(text: str) -> str:
    return text.lower()

def extract_words(text: str) -> set:
    return set(re.findall(r"\w+", normalize(text)))

def geo_score(text: str) -> float:
    return 1.2 if TR_LOCATIONS.intersection(extract_words(text)) else 1.0

def severity_predict(text: str) -> float:
    score = 1.0
    lowered = normalize(text)
    if "ölü" in lowered or "ölüm" in lowered: score += 0.4
    if "yaralı" in lowered: score += 0.2
    if "patlama" in lowered: score += 0.3
    return min(score, 1.5)

from datetime import datetime, timezone

def recency_weight(date_str: str) -> float:
    try:
        # Ensure that the article timestamp is timezone-naive
        article_time = datetime.fromisoformat(date_str).astimezone(timezone.utc).replace(tzinfo=None)
        # Get the current time as a naive datetime (also in UTC)
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Calculate time delta in seconds
        delta = (current_time - article_time).total_seconds()
        
        if delta < 3600:  # Less than 1 hour
            return 1.5
        elif delta < 86400:  # Less than 24 hours
            return 1.2
        elif delta < 3 * 86400:  # Less than 3 days
            return 1.0
        else:
            return 0.8
    except Exception as e:
        logging.error(f"Invalid timestamp: {e}")
        return 1.0

def engagement_score(views: int, likes: int, comments: int) -> float:
    return min(1.5, 1.0 + 0.00005 * views + 0.01 * likes + 0.02 * comments)

def source_weight(source: str) -> float:
    return SOURCE_WEIGHTS.get(normalize(source), 1.0)

def hot_topic_score(text: str, hot_topics: set) -> float:
    return 1.2 if hot_topics.intersection(extract_words(text)) else 1.0

@lru_cache(maxsize=1)
def fetch_trending_titles() -> set:
    try:
        response = requests.get("https://trends.google.com/trends/trendingsearches/daily/rss?geo=TR")
        titles = set(re.findall(r"<title>(.*?)</title>", response.text, re.DOTALL))
        trending = {normalize(t) for t in titles if len(t.split()) < 8}
        logging.info(f"Fetched {len(trending)} trending titles")
        return trending
    except Exception as e:
        logging.warning(f"Failed to fetch trending titles: {e}")
        return set()
    
# --- Routes ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the News Ranking API. Use the /rank endpoint to post news articles."}

@app.post("/rank", response_model=List[NewsRankedResponse])
def rank_articles(request: NewsRankRequest):
    trending_titles = fetch_trending_titles()

    results = []
    for article in request.articles:
        title = article.title
        content = article.content

        scores = {
            "source": source_weight(article.source),
            "recency": recency_weight(article.timestamp),
            "engagement": engagement_score(article.views, article.likes, article.comments),
            "geo": geo_score(f"{title} {content}"),
            "severity": severity_predict(f"{title} {content}"),
            "trend": hot_topic_score(f"{title} {content}", HOT_TOPICS.union(trending_titles)),
        }

        total_score = sum(SCORE_WEIGHTS[key] * scores[key] for key in scores)

        results.append(NewsRankedResponse(
            article=article,
            score=round(total_score, 3),
            details=scores if request.debug else None
        ))

    return sorted(results, key=lambda x: x.score, reverse=True)
