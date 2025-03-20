from django.urls import path
from .views.userViews import (
    ListUsersView,
    SavePreferredCategoriesView,
    # DeleteNonSuperusersView,  # Import the new view
)
from .views.articleViews import ArticleListView, InsertArticlesView, delete_articles, get_articles
from .views.authViews import RegisterView, LoginView

urlpatterns = [
    # User views
    path('users/', ListUsersView.as_view(), name='list-users'),
    path('save-preferences/', SavePreferredCategoriesView.as_view(), name='save-preferences'),
    # path('delete-non-superusers/', DeleteNonSuperusersView.as_view(), name='delete-non-superusers'),  # Add this line

    # Article views
    path('articles/', ArticleListView.as_view(), name='article-list'),
    path('insert-articles/', InsertArticlesView.as_view(), name='insert-articles'),
    path('delete-articles/<int:_id>/', delete_articles, name='delete-articles'),
    path('get-articles/', get_articles, name='get-articles'),

    # Auth views
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
]