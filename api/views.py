from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Article
from .serializers import ArticleSerializer
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.http import JsonResponse
from django.db.models import Q
import json
import os
import uuid
from django.conf import settings


class ArticleListView(APIView):
    def get(self, request, *args, **kwargs):
        articles = Article.objects.all()  # Get all articles
        serializer = ArticleSerializer(articles, many=True)  # Serialize the articles
        return Response(serializer.data)  # Return serialized data as a response
    
# ✅ Correct the directory path
GENERATED_ARTICLES_DIR = "ADD_YOUR_PATH_HERE"  # Add your path here

# ✅ Debugging: Print the actual path
print("Checking path:", GENERATED_ARTICLES_DIR)

# ✅ Ensure directory exists
if not os.path.exists(GENERATED_ARTICLES_DIR):
    print("⚠️ ERROR: The directory does not exist!")
    os.makedirs(GENERATED_ARTICLES_DIR)  # ✅ Create it automatically
    print("✅ Directory created:", GENERATED_ARTICLES_DIR)
# ✅ Convert to an APIView

        
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
                return JsonResponse({"message": f"No article with id {_id} is found, make sure to input articleID (uuid)!"})
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)