"""
news_rank_service.py
FastAPI service that ranks news articles based on recency, engagement, and severity.
"""

from __future__ import annotations
import re, datetime as dt, warnings
from functools import lru_cache
from typing import List

import numpy as np
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel, Field

# ------------------------------
# 1.  Pydantic schema
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
# 2.  Lightweight “models”
# ------------------------------
# 2‑A  Severity score
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
    return min(score, 1.0)

# 2‑B  Location boost
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
                return 1.0
        return 0.0
    return 1.0 if re.search(r"(Türkiye|Ankara|İstanbul|İzmir)", body, re.I) else 0.0

# ------------------------------
# 3.  API + Endpoint
# ------------------------------
router = APIRouter(prefix="/v1")

@router.post("/rank")
def rank(
    articles: List[Article],
    genre: str | None = None,
    country: str = "TR"
):
    now = dt.datetime.now(dt.timezone.utc)
    ranked = []

    for art in articles:
        hours = (now - art.published_at).total_seconds() / 3600
        rec = np.exp(-hours / 6)  # Half-life ≈6h
        eng = np.sqrt(art.clicks + 2 * art.shares)
        sev = severity_predict(f"{art.title} {art.body}", genre)
        geo = place_boost(art.body, country)

        score = (0.25 * art.source_score +
                 0.25 * rec +
                 0.20 * eng +
                 0.20 * geo +
                 0.10 * sev)

        ranked.append({"id": art.id, "score": round(float(score), 6)})

    return sorted(ranked, key=lambda x: x["score"], reverse=True)

# ------------------------------
# 4.  App registration
# ------------------------------
app = FastAPI(title="News‑ranking‑API", version="0.1.0")
app.include_router(router)
