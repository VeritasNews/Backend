from django.urls import path
from .views.userViews import (
    ListUsersView,
    SavePreferredCategoriesView,
    # DeleteNonSuperusersView,  # Import the new view
)
from .views.articleViews import ArticleListView, InsertArticlesView, delete_articles, get_articles, get_article_by_id
from .views.authViews import RegisterView, LoginView
from .views.likeViews import like_article, unlike_article, get_liked_articles

urlpatterns = [
    # User views
    path('users/', ListUsersView.as_view(), name='list-users'),
    path('save_preferences/', SavePreferredCategoriesView.as_view(), name='save_preferences'),
    # path('delete-non-superusers/', DeleteNonSuperusersView.as_view(), name='delete-non-superusers'),  # Add this line

    # Article views
    path('articles/', ArticleListView.as_view(), name='article-list'),
    path('insert_articles/', InsertArticlesView.as_view(), name='insert-articles'),
    path('delete_articles/', delete_articles, name='delete-articles'),
    path('get_articles/', get_articles, name='get_articles'),
    path('articles/<int:pk>/', get_article_by_id, name='get_article_by_id'),

    # Auth views
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    
    # Like views
    path('articles/<str:article_id>/like/', like_article, name='like_article'),
    path('articles/<str:article_id>/unlike/', unlike_article, name='unlike_article'),
    path("users/me/liked_articles/", get_liked_articles, name="liked_articles"),
]