from __future__ import annotations
import re
import datetime as dt
import warnings
import logging
from functools import lru_cache
from typing import List

import numpy as np
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel, Field

# ------------------------------
# Logging setup
# ------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

import requests

NEWSAPI_KEY = "5eed6c8440a84ac69345abfbae4505c8"

def fetch_trending_titles():
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": NEWSAPI_KEY,
        "country": "tr",
        "pageSize": 20,
    }
    try:
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()
        return [a["title"].lower() for a in data.get("articles", []) if a.get("title")]
    except Exception as e:
        logger.warning(f"NewsAPI fetch failed: {e}")
        return []

from difflib import SequenceMatcher

def compute_trending_score(article_title: str, trending_titles: list[str]) -> float:
    article_title = article_title.lower()
    similarities = [
        SequenceMatcher(None, article_title, trend_title).ratio()
        for trend_title in trending_titles
    ]
    max_similarity = max(similarities, default=0.0)
    return round(min(max_similarity, 1.0), 3)  # Keep it bounded


# ------------------------------
# 1. Pydantic schema
# ------------------------------
class Article(BaseModel):
    id: str
    title: str
    body: str
    source_score: float = Field(ge=0, le=1)
    published_at: dt.datetime
    clicks: int = Field(ge=0)
    shares: int = Field(ge=0)


# ------------------------------
# 2. Lightweight “models”
# ------------------------------

_SEVERITY = {
    "earthquake": 1.0, "deprem": 1.0,
    "election": .9, "seçim": .9,
    "coup": .95, "darbe": .95,
    "protest": .8, "gösteri": .8,
}
def severity_predict(text: str, genre: str | None) -> float:
    txt = text.lower()
    score = max((_SEVERITY[k] for k in _SEVERITY if k in txt), default=.2)
    if genre and genre.lower() == "politics":
        score += 0.05
    result = min(score, 1.0)
    logger.debug(f"[Severity] Score: {result:.3f} for genre='{genre}' and text='{text[:30]}...'")
    return result


HOT_TOPICS = {
    "1 mayıs", "taksim", "kadıköy", "anayasa", "gençlik",
    "deprem", "ekonomi", "enflasyon", "gazze", "öğrenci", "özgür özel", "erdoğan", "önder"
}
def topic_trend_boost(text: str) -> float:
    lowered = text.lower()
    boost = 1.2 if any(topic in lowered for topic in HOT_TOPICS) else 1.0
    logger.debug(f"[Topic] Boost: {boost} for text='{text[:30]}...'")
    return boost


def recency_weight(published_at: dt.datetime, genre: str = "politics") -> float:
    now = dt.datetime.now(dt.timezone.utc)
    hours = (now - published_at).total_seconds() / 3600
    half_life = 4 if genre == "politics" else 12
    weight = np.exp(-hours / half_life)
    logger.debug(f"[Recency] Hours ago: {hours:.2f}, Weight: {weight:.3f}")
    return weight


_TURK_LOCS = {"türkiye", "ankara", "istanbul", "izmir"}
@lru_cache(maxsize=None)
def _load_spacy_tr():
    try:
        import spacy
        return spacy.load("tr_core_news_sm")
    except (OSError, ModuleNotFoundError):
        warnings.warn("spaCy Turkish model not found – using regex fallback.")
        return None

def place_boost(body: str, iso: str = "TR") -> float:
    nlp = _load_spacy_tr()
    if nlp:
        for ent in nlp(body).ents:
            if ent.label_ == "LOC" and ent.text.lower() in _TURK_LOCS:
                logger.debug("[Geo] spaCy location match found.")
                return 1.0
        return 0.0
    matched = bool(re.search(r"(Türkiye|Ankara|İstanbul|İzmir)", body, re.I))
    logger.debug(f"[Geo] Regex match: {matched}")
    return 1.0 if matched else 0.0


def time_weight() -> float:
    hour = dt.datetime.now().hour
    weight = 1.2 if 7 <= hour <= 11 else 1.0
    logger.debug(f"[Time] Hour={hour}, Weight={weight}")
    return weight


# ------------------------------
# 3. API endpoint
# ------------------------------
router = APIRouter(prefix="/v1")

@router.post("/rank")
def rank(
    articles: List[Article],
    genre: str | None = None,
    country: str = "TR"
):
    trending_titles = fetch_trending_titles()
    ranked = []
    logger.info(f"Received {len(articles)} articles for ranking.")

    for art in articles:
        title = art.title or ""
        body = art.body or ""
        full_text = f"{title} {body}"

        rec = recency_weight(art.published_at, genre or "")
        eng = np.sqrt(art.clicks + 2 * art.shares)
        sev = severity_predict(full_text, genre)
        geo = place_boost(body, country)
        src = art.source_score

        topic_boost = topic_trend_boost(full_text)
        time_boost = time_weight()
        trend_score = compute_trending_score(title, trending_titles)

        base_score = (
            0.18 * src +
            0.20 * rec +
            0.20 * eng +
            0.17 * geo +
            0.15 * sev +
            0.10 * trend_score
        )
        final_score = base_score * topic_boost * time_boost

        logger.info(
            f"[{art.id}] Trend={trend_score:.3f}, Final={final_score:.4f}"
        )

        ranked.append({
            "id": art.id,
            "score": round(float(final_score), 6)
        })

    return sorted(ranked, key=lambda x: x["score"], reverse=True)


# ------------------------------
# 4. App
# ------------------------------
app = FastAPI(title="News‑ranking‑API", version="0.2.0")
app.include_router(router)
