from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from api.models import Article
from api.serializers import ArticleSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_article(request, article_id):
    try:
        article = Article.objects.get(articleId=article_id)
        user = request.user
        user.likedArticles.add(article)
        return Response({'message': 'Article liked.'}, status=status.HTTP_200_OK)
    except Article.DoesNotExist:
        return Response({'error': 'Article not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unlike_article(request, article_id):
    try:
        article = Article.objects.get(articleId=article_id)
        user = request.user
        user.likedArticles.remove(article)
        return Response({'message': 'Article unliked.'}, status=status.HTTP_200_OK)
    except Article.DoesNotExist:
        return Response({'error': 'Article not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_liked_articles(request):
    user = request.user
    liked_articles = user.likedArticles.all()
    serializer = ArticleSerializer(liked_articles, many=True, context={'request': request})
    return Response(serializer.data)