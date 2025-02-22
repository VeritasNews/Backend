from django.urls import path
from .views import ArticleListView, insert_articles

urlpatterns = [
     path('articles/', ArticleListView.as_view(), name='article-list'),
    path('insert_articles/', insert_articles, name='insert-articles'),  # Add this line
]
