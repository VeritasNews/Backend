from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Article
from .serializers import ArticleSerializer
from django.http import JsonResponse

class ArticleListView(APIView):
    def get(self, request, *args, **kwargs):
        articles = Article.objects.all()  # Get all articles
        serializer = ArticleSerializer(articles, many=True)  # Serialize the articles
        return Response(serializer.data)  # Return serialized data as a response

def insert_articles(request):
    articles = [
        {"title": "Grevcilerin Destek Kazanması", "content": "Grevin desteği arttıkça daha fazla vatandaş protestolara katılarak, sistemik değişiklikler için baskı yapıyor.", "date": "2024-12-20", "image_path": None},
        {"title": "İşçiler Daha İyi Koşullar Talep Ediyor", "content": "Grevciler, daha iyi maaşlar ve çalışma koşulları talep ediyor, bu da ülke genelinde işçi haklarıyla ilgili tartışmaları tetikliyor.", "date": "2024-12-19", "image_path": "path_to_image/image2.jpg"},
        {"title": "Hükümetin Tutumu", "content": "Hükümet yetkilileri, kesintilerin sona ermesini ve normale dönülmesini isteyen kararlı bir tutum sergiliyor.", "date": "2024-12-18", "image_path": None},
        # Add the rest of the articles...
    ]
    
    for article in articles:
        # If using ImageField, handle image paths differently
        image = article['image_path'] if article['image_path'] else None
        
        Article.objects.create(
            title=article['title'],
            content=article['content'],
            date=article['date'],
            image=image  # Use the field name 'image' or 'image_path' based on your model
        )
    
    return JsonResponse({"message": "Articles inserted successfully!"})