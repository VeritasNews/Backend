from rest_framework import serializers
from .models import Article, User

from rest_framework import serializers
from .models import Article, User

class ArticleSerializer(serializers.ModelSerializer):
    liked_by_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id',
            'articleId',
            'title',
            'summary',
            'longerSummary',
            'category',
            'tags',
            'source',
            'location',
            'popularityScore',
            'createdAt',
            'image',
            'priority',  # 👈 Make sure this is included manually
            'liked_by_count',
            'is_liked',
        ]


    def get_liked_by_count(self, obj):
        if hasattr(obj, 'liked_by_users'):
            return obj.liked_by_users.count()
        return 0  # fallback if running on dict-like data

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, "user") and request.user.is_authenticated:
            return obj in request.user.likedArticles.all()
        return False



class PrivacySettingsSerializer(serializers.Serializer):
    liked_articles = serializers.ChoiceField(choices=['public', 'friends', 'private'])
    reading_history = serializers.ChoiceField(choices=['public', 'friends', 'private'])
    friends_list = serializers.ChoiceField(choices=['public', 'friends', 'private'])
    profile_info = serializers.ChoiceField(choices=['public', 'friends', 'private'])
    activity_status = serializers.ChoiceField(choices=['public', 'friends', 'private'])

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = '__all__'  # or make sure 'preferredCategories' is listed in fields

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data, password=password)
        return user

    def _can_view_field(self, field_name, target_user):
        request = self.context.get("request")
        if not request or not hasattr(request, "user"):
            return False
        viewer = request.user
        privacy_level = target_user.privacySettings.get(field_name, 'private')

        if viewer == target_user:
            return True
        elif privacy_level == 'public':
            return True
        elif privacy_level == 'friends' and viewer in target_user.friends.all():
            return True
        return False

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if not self._can_view_field('liked_articles', instance):
            data['likedArticles'] = []

        if not self._can_view_field('reading_history', instance):
            data['readingHistory'] = []

        if not self._can_view_field('friends_list', instance):
            data['friends'] = []

        request = self.context.get("request")
        viewer = getattr(request, "user", None)

        # 🔓 Allow user to see their own profile info
        if not self._can_view_field('profile_info', instance) and viewer != instance:
            data['email'] = None
            data['location'] = None

        return data
