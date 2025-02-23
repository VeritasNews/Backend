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
        {
            "articleId": "1",
            "title": "Bahçeli, Öcalan'ı Mecliste Konuşmaya Çağırıyor: Silah Bırakımını İlan Etmeli",
            "content": "Bahçeli, Öcalan'ı Meclis'te DEM grubunda silahları bırakıp terörün sonunu ilan etmeye çağırdı.  \"Umut Hakkı\"ndan yararlanma teklifini de gündeme getirdi.",
            "summary": "Bahçeli, Öcalan'ı Meclis'te konuşmaya çağırdı.",
            "longerSummary": "MHP lideri Bahçeli, Öcalan'ın Meclis'te DEM partisine gelerek terörün sonlandığını ilan etmesini istedi. Bu adımın \"umut hakkı\" yasasıyla Öcalan'ın serbest kalmasının önünü açabileceğini belirtti.",
            "category": "Politics",
            "tags": ["Politics", "Turkey"],
            "source": "Local News",
            "location": "Ankara",
            "popularityScore": 100,
            "image": None,
        },
        {
            "articleId": "2",
            "title": "Erdoğan, Sudan Egemenlik Konseyi Başkanı ile Görüştü",
            "content": "Cumhurbaşkanı Erdoğan, Sudan Egemenlik Konseyi Başkanı Burhan ile görüştü.  Görüşmede Türkiye-Sudan ilişkileri, bölgesel konular ve Türkiye'nin Somali-Etiyopya anlaşmazlığındaki rolü ele alındı. Erdoğan, Sudan-BAE ihtilafında da arabuluculuk teklif etti.",
            "summary": "Erdoğan, Sudan lideri ile görüştü.",
            "longerSummary": "Cumhurbaşkanı Erdoğan, Sudan Egemenlik Konseyi Başkanı Burhan ile bir araya geldi. Görüşmede bölgesel konular ve Türkiye'nin arabuluculuk rolü ele alındı.",
            "category": "International",
            "tags": ["Erdoğan", "Sudan"],
            "source": "International News",
            "location": "Sudan",
            "popularityScore": 85,
            "image": None,
        },
        # Add the rest of the articles...
    ]

    for article in articles:
        Article.objects.create(
            articleId=article['articleId'],
            title=article['title'],
            content=article['content'],
            summary=article['summary'],
            longerSummary=article['longerSummary'],
            category=article['category'],
            tags=article['tags'],
            source=article['source'],
            location=article['location'],
            popularityScore=article['popularityScore'],
            image=article['image'],
        )
    
    return JsonResponse({"message": "Articles inserted successfully!"})