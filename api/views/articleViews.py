from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.db.models import Q
import json
import os
import uuid
import logging
from rest_framework import status
from api.models import Article
from api.serializers import ArticleSerializer
from django.db.models import Count

logger = logging.getLogger(__name__)

from api.utils.news_ranker import rank_articles

class ArticleListView(APIView):
    def get(self, request, *args, **kwargs):
        # In articleViews.py → ArticleListView or wherever you query Articles
        articles = list(
            Article.objects.all().prefetch_related('liked_by_users')
        )

        rankings = rank_articles(articles, genre="politics", country="TR")
        score_map = {r["id"]: r["score"] for r in rankings}

        # Sort by score
        articles.sort(key=lambda a: score_map.get(str(a.articleId), 0), reverse=True)

        serializer = ArticleSerializer(articles, many=True, context={'request': request})
        return Response(serializer.data)


# Directory path for JSON files
GENERATED_ARTICLES_DIR = r"C:\Users\zeyne\Desktop\bitirme\VeritasNews\News-Objectify\objectified_jsons"

# Ensure directory exists
if not os.path.exists(GENERATED_ARTICLES_DIR):
    os.makedirs(GENERATED_ARTICLES_DIR)  # Create it automatically

class InsertArticlesView(APIView):
    def post(self, request, *args, **kwargs):
        inserted_count = 0
        errors = []

        try:
            for filename in os.listdir(GENERATED_ARTICLES_DIR):
                if filename.endswith(".json"):
                    filepath = os.path.join(GENERATED_ARTICLES_DIR, filename)

                    with open(filepath, 'r', encoding='utf-8') as file:
                        try:
                            data = json.load(file)

                            # ✅ Debugging: Print data before inserting
                            print(f"📥 Received JSON from {filename}: {json.dumps(data, indent=2)}")

                            # ✅ Extract fields with defaults
                            title = data.get("title", "").strip() or None
                            summary = data.get("summary", "").strip() or None
                            longer_summary = data.get("longerSummary", "").strip() or None
                            source = data.get("source", []) or None
                            article_id = data.get("articleId", str(uuid.uuid4()))
                            priority = data.get("priority", None)

                            if priority == "most":
                                Article.objects.filter(priority="most").update(priority="high")  # downgrade previous "most"

                            # ✅ Allow inserting even if title is missing
                            Article.objects.create(
                                articleId=article_id,
                                title=title,  # Allow None
                                summary=summary,  # Allow None
                                longerSummary=longer_summary,  # Allow None
                                source=source,  # Allow None
                                content="",
                                category = data.get("category", None),
                                tags=[],
                                location=None,
                                popularityScore=0,
                                image=None,
                                priority=priority  # ✅ <- THIS LINE IS MISSING
                            )
                            inserted_count += 1

                        except json.JSONDecodeError:
                            errors.append(f"❌ Failed to parse {filename}: Invalid JSON.")
                        except Exception as e:
                            errors.append(f"❌ Error inserting {filename}: {str(e)}")

            return Response({
                "message": f"✅ Successfully inserted {inserted_count} unique articles.",
                "errors": errors
            }, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

from rest_framework.parsers import MultiPartParser, FormParser

class InsertSingleArticleView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        json_data = request.data.get('data')
        image = request.FILES.get('image')

        try:
            data = json.loads(json_data)

            article = Article.objects.create(
                articleId = data.get("articleId", str(uuid.uuid4())),
                title = data.get("title", ""),
                summary = data.get("summary", ""),
                longerSummary = data.get("longerSummary", ""),
                content = data.get("content", ""),
                category = data.get("category", ""),
                tags = data.get("tags", []),
                source = data.get("source", ""),
                location = data.get("location", ""),
                popularityScore = data.get("popularityScore", 0),
                createdAt = data.get("createdAt", None),
                priority = data.get("priority", None),
                image = image
            )

            return Response({"message": "✅ Article inserted successfully!"}, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=400)


def delete_articles(request, _id=-1):
    """
    Deletes articles based on the given id.
    - If id is -1, all articles will be deleted.
    - If an article with the given id exists, it will be deleted.
    - If no matching article is found, an error message will be returned.
    """
    try:
        if _id == -1:
            deleted_count, _ = Article.objects.all().delete()
            return JsonResponse({"message": f"Deleted all {deleted_count} articles successfully!"})
        else:
            deleted_count, _ = Article.objects.filter(articleId=_id).delete()
            if deleted_count > 0:
                return JsonResponse({"message": f"Deleted {deleted_count} article(s) with id {_id} successfully!"})
            else:
                return JsonResponse({"message": f"No article with id {_id} found."})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

import requests
from api.models import Article
from api.serializers import ArticleSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response

RANKING_API_URL = "https://ranker-service.onrender.com/v1/rank"

@api_view(['GET'])
def get_articles(request):
    category = request.GET.get('category', None)

    articles = Article.objects.all()
    if category:
        articles = articles.filter(category__iexact=category)

    serializer = ArticleSerializer(articles, many=True)
    serialized_data = serializer.data

    # Prepare payload for FastAPI ranking
    ranking_payload = [
        {
            "id": str(a["articleId"]),
            "title": a["title"] or "",
            "body": a["longerSummary"] or a["summary"] or "",
            "source_score": 0.8,
            "published_at": a["createdAt"] or "2025-01-01T00:00:00Z",
            "clicks": a["popularityScore"] or 0,
            "shares": a.get("liked_by_count", 0)
        }
        for a in serialized_data
    ]

    try:
        rank_response = requests.post(RANKING_API_URL, json=ranking_payload, params={
            "genre": category,
            "country": "TR"
        })
        rank_data = rank_response.json()
        score_map = {r["id"]: r["score"] for r in rank_data}
        # Sort original data by score
        sorted_articles = sorted(serialized_data, key=lambda a: score_map.get(str(a["articleId"]), 0), reverse=True)
        return Response(sorted_articles)

    except Exception as e:
        print("⚠️ Ranking API failed:", str(e))
        return Response(serialized_data)


@api_view(['GET'])
def get_article_by_id(request, pk):
    try:
        article = Article.objects.get(pk=pk)
        serializer = ArticleSerializer(article, context={'request': request})  # 👈 FIX HERE
        logger.info(f"Fetched article with ID: {pk}")
        return Response(serializer.data)
    except Article.DoesNotExist:
        logger.warning(f"Article with ID {pk} not found.")
        return Response({"error": "Article not found."}, status=status.HTTP_404_NOT_FOUND)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from api.models import Article
from api.serializers import ArticleSerializer

class PersonalizedArticleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        preferred_categories = user.preferredCategories or []

        preferred_articles = Article.objects.filter(category__in=preferred_categories)
        other_articles = Article.objects.exclude(category__in=preferred_categories)

        all_articles = list(preferred_articles) + list(other_articles)

        serializer = ArticleSerializer(all_articles, many=True)
        return Response(serializer.data)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from api.models import Article, ArticleInteraction

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_article_interaction(request):
    user = request.user
    data = request.data
    try:
        article = Article.objects.get(pk=data['articleId'])
        interaction = ArticleInteraction.objects.create(
            user=user,
            article=article,
            action=data['action'],
            time_spent=data.get('time_spent')
        )

        # ✅ Recalculate popularity score after new interaction
        views = ArticleInteraction.objects.filter(article=article, action='view').count()
        likes = ArticleInteraction.objects.filter(article=article, action='like').count()
        clicks = ArticleInteraction.objects.filter(article=article, action='click').count()
        shares = ArticleInteraction.objects.filter(article=article, action='share').count()

        # 🧠 Weighted popularity score formula (adjust weights as needed)
        score = views + (2 * likes) + (1.5 * clicks) + (3 * shares)
        article.popularityScore = int(score)
        article.save()

        # ✅ Trigger model retraining script
        from subprocess import Popen
        import sys
        import os
        from django.core.cache import cache
        from datetime import datetime, timedelta

        script_path = os.path.join(os.path.dirname(__file__), 'article_priorization.py')

        last_run = cache.get("last_model_training", None)
        now = datetime.now()

        if not last_run or (now - last_run) > timedelta(minutes=10):
            cache.set("last_model_training", now, timeout=600)
            Popen([sys.executable, script_path])

        return Response({'message': 'Logged, score updated, & retraining triggered ✅'}, status=201)

    except Exception as e:
        return Response({'error': str(e)}, status=400)


# 🧠 FIXED: build_features — includes user preferences
from django.db import models
from django.utils import timezone

def build_features(user, article):
    categories = [
        "Siyaset", "Entertainment", "Spor", "Teknoloji", "Saglik", "Cevre", "Bilim", "Egitim",
        "Ekonomi", "Seyahat", "Moda", "Kultur", "Suc", "Yemek", "YasamTarzi", "IsDunyasi",
        "DunyaHaberleri", "Oyun", "Otomotiv", "Sanat", "Tarih", "Uzay", "Iliskiler", "Din",
        "RuhSagligi", "Magazin"
    ]
    priorities = ['high', 'medium', 'low']

    interactions = ArticleInteraction.objects.filter(user=user, article=article)
    views = interactions.filter(action='view').count()
    likes = interactions.filter(action='like').count() * 2  # Give more weight to likes
    clicks = interactions.filter(action='click').count() * 1.5  # Give more weight to clicks
    shares = interactions.filter(action='share').count() * 3  # Give most weight to shares
    time_spent = interactions.aggregate(avg_time=models.Avg("time_spent"))['avg_time'] or 0

    # Category and priority one-hot
    category_features = [1 if article.category == c else 0 for c in categories]
    priority_features = [1 if article.priority == p else 0 for p in priorities]
    
    # Add a special feature for "most" priority
    is_most_priority = 1 if article.priority == "most" else 0

    # User preference match — boosts based on match with preferredCategories
    user_pref = getattr(user, 'preferredCategories', []) or []
    preference_match = [5 if article.category in user_pref else 0]  # Stronger weight

    # Recency feature (days since publication, capped at 7)
    days_old = 7
    if article.createdAt:
        days_old = min(7, (timezone.now() - article.createdAt).days)
    recency_feature = [max(0, 7 - days_old) / 7]  # 1.0 for today, 0.0 for a week old

    # Popularity score feature
    popularity = [min(1.0, article.popularityScore / 100.0)]  # Normalize to 0-1

    raw_features = [
        time_spent, likes, clicks, views, shares, is_most_priority
    ] + category_features + priority_features + preference_match + recency_feature + popularity

    return [float(f) if isinstance(f, (int, float)) and not pd.isna(f) else 0.0 for f in raw_features]

from django.contrib.auth import get_user_model
from api.models import Article, UserArticleScore
import numpy as np
import pandas as pd
import joblib
import os

User = get_user_model()

# Load model and features
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'recommender_model.pkl')
FEATURE_PATH = os.path.join(os.path.dirname(__file__), 'model_features.pkl')
model = joblib.load(MODEL_PATH)
feature_columns = joblib.load(FEATURE_PATH)

def assign_priority(user=None):
    if user:
        users = [user]
    else:
        users = User.objects.all()

    articles = Article.objects.all()
    print(f"👥 Users: {len(users)} | 📰 Articles: {articles.count()}")

    # First, identify any article with original "most" priority (breaking news)
    breaking_news = list(articles.filter(priority="most"))
    has_breaking_news = len(breaking_news) > 0
    
    for user in users:
        user_scores = []
        user_preferred_categories = getattr(user, 'preferredCategories', []) or []

        for article in articles:
            # Get model score
            raw_features = build_features(user, article)
            df = pd.DataFrame([raw_features])
            df = df.reindex(columns=feature_columns, fill_value=0)

            try:
                model_score = float(model.predict_proba(df)[0][1])
                if np.isnan(model_score):
                    raise ValueError("NaN score")
            except Exception:
                model_score = 0.5  # default fallback
            
            # Apply additional boosting factors
            final_score = model_score
            
            # Boost for articles with "most" priority (breaking news)
            if article.priority == "most":
                final_score *= 2.5  # Higher boost for breaking news
            
            # Boost for articles in user's preferred categories
            if article.category in user_preferred_categories:
                final_score *= 1.5  # 50% boost for preferred categories
            
            # Recency boost (for newer articles)
            if article.createdAt:
                time_diff = timezone.now() - article.createdAt
                if time_diff.days < 1:  # Less than a day old
                    hours_old = time_diff.seconds / 3600
                    if hours_old < 6:
                        final_score *= 1.3  # 30% boost for very recent news
            
            user_scores.append((article, final_score))

        # Sort by final score
        user_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Assign priority based on position and score
        label_counts = {"most": 0, "high": 0, "medium": 0, "low": 0}
        
        # First pass: assign most to breaking news, otherwise to top article
        for idx, (article, score) in enumerate(user_scores):
            if article.priority == "most":
                label = "most"  # Preserve existing breaking news priority
            elif idx == 0 and not has_breaking_news:
                label = "most"  # Top article becomes "most" if no breaking news exists
            elif idx < 5:  # Top 5 articles
                label = "high"
            elif idx < 15:  # Next 10 articles
                label = "medium"
            else:
                label = "low"
                
            label_counts[label] += 1
            
            UserArticleScore.objects.update_or_create(
                user=user,
                article=article,
                defaults={"score": score, "priority": label}
            )

        print(f"✅ Assigned {len(user_scores)} articles for {user.email} → {label_counts}")
                
def extract_user_features(user):
    # You can later use things like time of day, recent activity, etc.
    return {}

import os
import joblib

# Load model from the same directory as this file
# Load model and expected feature order
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'recommender_model.pkl')
FEATURE_PATH = os.path.join(os.path.dirname(__file__), 'model_features.pkl')

model = joblib.load(MODEL_PATH)
feature_columns = joblib.load(FEATURE_PATH)  # list of expected feature names

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.models import Article, UserArticleScore
from api.serializers import ArticleSerializer
import requests
from datetime import datetime, timedelta

RANKING_API_URL = "https://ranker-service.onrender.com/v1/rank"

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def personalized_feed(request):
    from datetime import datetime, timezone
    import numpy as np

    user = request.user
    all_articles = Article.objects.all()

    # ML scores from DB
    scored_qs = UserArticleScore.objects.filter(user=user)
    ml_scores = {s.article.articleId: s.score for s in scored_qs}
    ml_priorities = {s.article.articleId: s.priority for s in scored_qs}

    # Send ALL to FastAPI
    payload = [
        {
            "id": str(a.articleId),
            "title": a.title or "",
            "body": a.longerSummary or a.summary or "",
            "source_score": 0.8,
            "published_at": a.createdAt.isoformat() if a.createdAt else "2025-01-01T00:00:00Z",
            "clicks": a.popularityScore or 0,
            "shares": 0
        }
        for a in all_articles
    ]

    try:
        res = requests.post(
            "https://ranker-service.onrender.com/v1/rank",
            json=payload,
            params={"genre": "politics", "country": "TR"},
            timeout=5
        )
        fastapi_scores = {r["id"]: r["score"] for r in res.json()}
    except Exception as e:
        print("⚠️ FastAPI ranker failed:", str(e))
        fastapi_scores = {}

    # Combine ML and FastAPI
    combined = []
    most_article_id = None
    highest_score = -1

    for article in all_articles:
        article_id = str(article.articleId)
        ml_score = ml_scores.get(article_id, 0.5)
        fastapi_score = fastapi_scores.get(article_id, 0.5)

        created_at = article.createdAt
        if not isinstance(created_at, datetime):
            try:
                created_at = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
            except Exception:
                created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

        hours_since_pub = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
        recency_weight = np.exp(-hours_since_pub / 6)

        hybrid_score = ((0.3 * ml_score + 0.2 * fastapi_score) + (0.5 * recency_weight))

        if hybrid_score > highest_score:
            most_article_id = article_id
            highest_score = hybrid_score

        priority = ml_priorities.get(article_id, "low")

        title_lower = (article.title or "").strip().lower()
        if title_lower in {"error", "failed to generate"}:
            continue  # 🚫 skip bad articles

        art_data = ArticleSerializer(article, context={'request': request}).data
        art_data['relevance_score'] = round(hybrid_score, 4)
        art_data['personalized_priority'] = priority
        combined.append(art_data)


    # Apply "most" to just one article if conditions matched
    if most_article_id:
        for a in combined:
            if str(a["articleId"]) == most_article_id:
                a["personalized_priority"] = "most"

    # Apply filters
    category = request.GET.get("category")
    priority = request.GET.get("priority")

    if category:
        combined = [a for a in combined if a.get("category") == category]
    if priority:
        combined = [a for a in combined if a.get("personalized_priority") == priority]

    # Sort by hybrid relevance
    combined.sort(
        key=lambda x: (
            round(float(x["relevance_score"]), 4),
            datetime.fromisoformat(x["createdAt"].replace("Z", "+00:00")) if x.get("createdAt") else datetime.min
        ),
        reverse=True
    )

    return Response(combined)