from django.urls import path
from .views import ArticleListView, delete_articles, InsertArticlesView

urlpatterns = [
    path('articles/', ArticleListView.as_view(), name='article-list'),
    path('insert_articles/', InsertArticlesView.as_view(), name='insert-articles'),  # Add this line
    path('delete_articles/', delete_articles, name='delete-articles'),  # Default (-1) deletes all
    path('delete_articles/<int:id>/', delete_articles, name='delete-article-by-id'),  # Pass article ID
]
