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
