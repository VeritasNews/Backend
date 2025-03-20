from rest_framework import serializers
from .models import Article, User

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = '__all__'  # Or specify the fields you want to include


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'userId',  # Include the UUID field
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