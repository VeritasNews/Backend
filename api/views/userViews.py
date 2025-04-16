from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser  # Add IsAdminUser
from api.models import User
from api.serializers import UserSerializer

class ListUsersView(APIView):
    def get(self, request):
        try:
            # Optimize the query to prefetch related Many-to-Many fields
            users = User.objects.all().prefetch_related(
                'likedArticles',  # Prefetch liked articles
                'readingHistory',  # Prefetch reading history
                'friends'  # Prefetch friends
            )
            
            # Serialize the users
            serializer = UserSerializer(users, many=True)
            
            # Return the serialized data
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            # Handle any unexpected errors
            return Response(
                {"error": "An error occurred while fetching users.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SavePreferredCategoriesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        categories = request.data.get("categories", [])

        if len(categories) < 5:
            return Response({"error": "Select at least 5 categories."}, status=status.HTTP_400_BAD_REQUEST)

        user.preferredCategories = categories
        user.save()

        return Response({"message": "Preferences updated successfully!"}, status=status.HTTP_200_OK)

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
# views/userViews.py
class GetUserByIdView(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(userId=user_id)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

from rest_framework.permissions import IsAdminUser

from rest_framework.permissions import IsAuthenticated, AllowAny  # Or AllowAny for no auth at all

class DeleteAllUsersView(APIView):
    permission_classes = [AllowAny]  # or [IsAuthenticated] if login required

    def delete(self, request):
        try:
            deleted_count, _ = User.objects.exclude(is_superuser=True).delete()
            return Response(
                {"message": f"Deleted {deleted_count} user(s)."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": "Failed to delete users.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

from rest_framework.parsers import MultiPartParser, FormParser

class UpdateProfilePictureView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request):
        user = request.user
        image = request.FILES.get("profile_picture")  # ✅ This must match the key in FormData

        if not image:
            return Response({"error": "No image file provided."}, status=400)

        user.profilePicture = image
        user.save()
        return Response({"message": "Profile picture updated successfully."})
