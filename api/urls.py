from django.urls import path, re_path
from .views.userViews import (
    ListUsersView,
    SavePreferredCategoriesView,
    # DeleteNonSuperusersView,  # Import the new view
    MeView,
    GetUserByIdView,  # Import the new view
    DeleteAllUsersView,  # Import the new view
    UpdateProfilePictureView,
    public_user_profile,
    UpdatePrivacySettingsView,
)
from .views.articleViews import InsertSingleArticleView, personalized_feed, log_article_interaction, ArticleListView, InsertArticlesView, delete_articles, get_articles, get_article_by_id
from .views.authViews import RegisterView, LoginView, PasswordResetRequestView, PasswordResetConfirmView
from .views.likeViews import like_article, unlike_article, get_liked_articles
from .views.friendViews import CombinedSearchView, FriendsWhoLikedArticleView, FriendsLikedArticlesView, FriendRequestListView, SendFriendRequestView, AcceptFriendRequestView, RejectFriendRequestView, ListFriendsView, SearchUsersView
from django.views.generic import TemplateView

class PasswordResetRedirectView(TemplateView):
    template_name = 'password_reset_redirect.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['uid'] = self.kwargs.get('uid')
        context['token'] = self.kwargs.get('token')
        context['deep_link'] = f"veritasnews://reset-password/{context['uid']}/{context['token']}"
        return context

urlpatterns = [
    # User views
    path('users/', ListUsersView.as_view(), name='list-users'),
    path('save_preferences/', SavePreferredCategoriesView.as_view(), name='save_preferences'),
    # path('delete-non-superusers/', DeleteNonSuperusersView.as_view(), name='delete-non-superusers'),  # Add this line
    path('users/delete_all/', DeleteAllUsersView.as_view(), name='delete_all_users'),
    path('users/update-profile-picture/', UpdateProfilePictureView.as_view(), name="update-profile-picture"),
    path("users/<uuid:user_id>/profile/", public_user_profile),
    path("user/privacy/", UpdatePrivacySettingsView.as_view()),
    
    # Article views
    path('articles/', ArticleListView.as_view(), name='article-list'),
    path('insert_articles/', InsertArticlesView.as_view(), name='insert-articles'),
    path('delete_articles/', delete_articles, name='delete-articles'),
    path('get_articles/', get_articles, name='get_articles'),
    path('articles/<int:pk>/', get_article_by_id, name='get_article_by_id'),
    # path("articles/for_you/", PersonalizedArticleListView.as_view()),
    path('log-interaction/', log_article_interaction),
    path("articles/for_you/", personalized_feed, name="personalized-feed"),
    path("insert_single_article/", InsertSingleArticleView.as_view(), name="insert_single_article"),
    
    # Auth views
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    re_path(r'^reset-password/(?P<uid>[\w-]+)/(?P<token>[\w-]+)/$', 
            PasswordResetRedirectView.as_view(), 
            name='password-reset-redirect'),
    
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
    path('articles/<int:article_id>/friends_liked/', FriendsWhoLikedArticleView.as_view(), name='friends-who-liked-article'),
    path('search/', CombinedSearchView.as_view(), name='combined-search'),
]
