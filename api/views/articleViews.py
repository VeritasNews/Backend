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

logger = logging.getLogger(__name__)

class ArticleListView(APIView):
    def get(self, request, *args, **kwargs):
        articles = Article.objects.all()  # Get all articles
        serializer = ArticleSerializer(articles, many=True, context={'request': request})
        return Response(serializer.data)  # Return serialized data as a response

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

@api_view(['GET'])
def get_articles(request):
    category = request.GET.get('category', None)  # Get category from query

    if category:
        category = category.strip()  # Remove extra spaces
        logger.info(f"Filtering by category: '{category}'")  # Log category
        articles = Article.objects.filter(category__iexact=category)  # Case-insensitive filtering
    else:
        articles = Article.objects.all()

    # Log only the count of articles being returned
    logger.info(f"Returning {articles.count()} articles.")
    serializer = ArticleSerializer(articles, many=True)
    return Response(serializer.data)

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

        # ✅ Trigger model retraining script
        from subprocess import Popen
        import sys
        import os

        script_path = os.path.join(os.path.dirname(__file__), 'article_priorization.py')
        # log timestamp in cache/db
        from django.core.cache import cache
        from datetime import datetime, timedelta

        last_run = cache.get("last_model_training", None)
        now = datetime.now()

        if not last_run or (now - last_run) > timedelta(minutes=10):
            cache.set("last_model_training", now, timeout=600)
            Popen([sys.executable, script_path])


        return Response({'message': 'Logged & retraining triggered ✅'}, status=201)

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def personalized_feed(request):
    user = request.user
    assign_priority(user)  # Re-score on access for freshness

    # Always get breaking news first
    breaking_news_scores = UserArticleScore.objects.filter(
        user=user, 
        priority="most"
    ).order_by('-score')
    
    # Then get other articles
    regular_scores = UserArticleScore.objects.filter(
        user=user
    ).exclude(priority="most").order_by('-score')
    
    # Combine them with breaking news always on top
    scores = list(breaking_news_scores) + list(regular_scores)
    
    # Optional filters 
    category_filter = request.GET.get('category')
    priority_filter = request.GET.get('priority')

    if category_filter:
        scores = [s for s in scores if s.article.category == category_filter.strip()]

    if priority_filter:
        scores = [s for s in scores if s.priority == priority_filter.strip()]

    # Fallback logic: return latest articles if nothing is scored
    if not scores:
        fallback_articles = Article.objects.all().order_by('-createdAt')[:20]
        serialized = ArticleSerializer(fallback_articles, many=True, context={'request': request})
        return Response(serialized.data)

    # Build response from scored articles
    top_articles = []
    for score_obj in scores[:30]:  # Top 30 personalized
        article_data = ArticleSerializer(score_obj.article, context={'request': request}).data
        article_data['personalized_priority'] = score_obj.priority
        article_data['relevance_score'] = float(score_obj.score)
        top_articles.append(article_data)

    return Response(top_articles)