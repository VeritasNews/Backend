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

                            # ✅ Allow inserting even if title is missing
                            Article.objects.create(
                                articleId=article_id,
                                title=title,  # Allow None
                                summary=summary,  # Allow None
                                longerSummary=longer_summary,  # Allow None
                                source=source,  # Allow None
                                content="",
                                category=None,
                                tags=[],
                                location=None,
                                popularityScore=0,
                                image=None
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
        return Response({'message': 'Logged'}, status=201)
    except Exception as e:
        return Response({'error': str(e)}, status=400)
   
def build_features(user, article):
    categories = [
        "Siyaset", "Entertainment", "Spor", "Teknoloji", "Saglik", "Cevre", "Bilim", "Egitim",
        "Ekonomi", "Seyahat", "Moda", "Kultur", "Suc", "Yemek", "YasamTarzi", "IsDunyasi",
        "DunyaHaberleri", "Oyun", "Otomotiv", "Sanat", "Tarih", "Uzay", "Iliskiler", "Din",
        "RuhSagligi", "Magazin"
    ]
    priorities = ['high', 'medium', 'low']

    category_features = [1 if article.category == c else 0 for c in categories]
    priority_features = [1 if article.priority == p else 0 for p in priorities]

    is_like = int(article in user.likedArticles.all())
    is_click = 0
    is_view = 1
    is_share = 0
    time_spent = 0.0

    return [time_spent, is_like, is_click, is_view, is_share] + category_features + priority_features

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

import numpy as np
import pandas as pd

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def personalized_feed(request):
    user = request.user
    preferred_categories = user.preferredCategories or []
    articles = Article.objects.all()
    article_scores = []

    for article in articles:
        raw_features = build_features(user, article)
        feature_df = pd.DataFrame([raw_features])
        feature_df = feature_df.reindex(columns=feature_columns, fill_value=0)

        proba = model.predict_proba(feature_df)[0]
        score = proba[1] if len(proba) > 1 else 0.0

        # 🚀 Boost for breaking news
        if article.priority == "high":
            score += 0.25

        # ❤️ Boost if user prefers this category
        if article.category in preferred_categories:
            score += 0.3  # ← tunable boost for preferred categories

        article_scores.append((article, score))

    article_scores.sort(key=lambda x: x[1], reverse=True)
    top_articles = [a for a, _ in article_scores[:30]]
    serializer = ArticleSerializer(top_articles, many=True, context={'request': request})
    return Response(serializer.data)
