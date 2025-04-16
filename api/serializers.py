from rest_framework import serializers
from .models import Article, User

from rest_framework import serializers
from .models import Article, User

class ArticleSerializer(serializers.ModelSerializer):
    liked_by_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = '__all__'  # Or specify manually if needed

    def get_liked_by_count(self, obj):
        return obj.liked_by_users.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, "user") and request.user.is_authenticated:
            return obj in request.user.likedArticles.all()
        return False


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'userId',  # Include the UUID field
            'userName',
            'name',
            'email',
            'password',
            'socialMediaId',
            'preferredCategories',
            'location',
            'isPremium',
            'likedArticles',  # Many-to-Many field
            'readingHistory',  # Many-to-Many field
            'friends',  # Many-to-Many field
            'notificationsEnabled',
            'privacySettings',
            'profilePicture',
            'is_active',
            'is_staff',
        ]

    def create(self, validated_data):
        # Extract the password and remove it from the validated data
        password = validated_data.pop('password')

        # Create the user
        user = User.objects.create_user(
            **validated_data,  # Pass all other fields
            password=password,  # Set the password separately
        )
        return user