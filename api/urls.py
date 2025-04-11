from django.urls import path
from .views.userViews import (
    ListUsersView,
    SavePreferredCategoriesView,
    # DeleteNonSuperusersView,  # Import the new view
    MeView,
    GetUserByIdView,  # Import the new view
    DeleteAllUsersView,  # Import the new view
)
from .views.articleViews import ArticleListView, InsertArticlesView, delete_articles, get_articles, get_article_by_id
from .views.authViews import RegisterView, LoginView
from .views.likeViews import like_article, unlike_article, get_liked_articles
from .views.friendViews import FriendsLikedArticlesView, FriendRequestListView, SendFriendRequestView, AcceptFriendRequestView, RejectFriendRequestView, ListFriendsView, SearchUsersView

urlpatterns = [
    # User views
    path('users/', ListUsersView.as_view(), name='list-users'),
    path('save_preferences/', SavePreferredCategoriesView.as_view(), name='save_preferences'),
    # path('delete-non-superusers/', DeleteNonSuperusersView.as_view(), name='delete-non-superusers'),  # Add this line
    path('users/delete_all/', DeleteAllUsersView.as_view(), name='delete_all_users'),


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
    path('users/me/', MeView.as_view(), name='user-me'),  # ✅ Add this route
    path('users/<uuid:user_id>/', GetUserByIdView.as_view(), name='get-user-by-id'),
    
    # Friend views
    path('friends/send/<uuid:user_id>/', SendFriendRequestView.as_view(), name='send-friend-request'),
    path('friends/accept/<uuid:user_id>/', AcceptFriendRequestView.as_view(), name='accept-friend-request'),
    path('friends/reject/<uuid:user_id>/', RejectFriendRequestView.as_view(), name='reject-friend-request'),
    path('friends/', ListFriendsView.as_view(), name='list-friends'),
    path('users/search/', SearchUsersView.as_view(), name='search-users'),
    path('friends/requests/', FriendRequestListView.as_view(), name='friend-requests'),
    path("articles/friends_liked/", FriendsLikedArticlesView.as_view(), name="friends-liked-articles"),
]