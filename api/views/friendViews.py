from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from api.models import FriendRequest, User

class SendFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        from_user = request.user
        print("From:", from_user.email)
        print("To User ID:", user_id)

        try:
            to_user = User.objects.get(userId=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        if from_user == to_user:
            return Response({'error': "You can't befriend yourself!"}, status=400)

        if FriendRequest.objects.filter(from_user=from_user, to_user=to_user).exists():
            return Response({'error': 'Friend request already sent.'}, status=400)

        FriendRequest.objects.create(
            from_user=from_user,
            to_user=to_user,
            status='pending'  # ✅ explicitly set status
        )

        return Response({'message': 'Friend request sent.'}, status=201)

class AcceptFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        from_user = User.objects.get(userId=user_id)
        to_user = request.user

        try:
            friend_request = FriendRequest.objects.get(from_user=from_user, to_user=to_user)
        except FriendRequest.DoesNotExist:
            return Response({'error': 'No friend request found.'}, status=status.HTTP_404_NOT_FOUND)

        # Confirm friendship
        from_user.friends.add(to_user)
        to_user.friends.add(from_user)
        friend_request.delete()

        return Response({'message': 'Friend request accepted.'}, status=status.HTTP_200_OK)

class RejectFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        from_user = User.objects.get(userId=user_id)
        to_user = request.user

        try:
            friend_request = FriendRequest.objects.get(from_user=from_user, to_user=to_user)
            friend_request.delete()
            return Response({'message': 'Friend request rejected.'}, status=status.HTTP_200_OK)
        except FriendRequest.DoesNotExist:
            return Response({'error': 'No friend request found.'}, status=status.HTTP_404_NOT_FOUND)

class ListFriendsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        friends = user.friends.all()
        data = [
            {
                'userId': f.userId,
                'name': f.name,
                'userName': f.userName,  # 👈 ADD THIS LINE
                'email': f.email,
            }
            for f in friends
        ]
        return Response(data)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from api.models import User
from api.serializers import UserSerializer
from django.db.models import Q

class SearchUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.GET.get("q", "")
        users = User.objects.filter(
            Q(name__icontains=query) | Q(userName__icontains=query)
        ).exclude(id=request.user.id)

        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from api.models import FriendRequest
from api.serializers import UserSerializer  # Make sure this includes userId, name, userName

class FriendRequestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all pending friend requests sent *to* the current user
        incoming_requests = FriendRequest.objects.filter(to_user=request.user, status='pending')
        
        # Return minimal info about the sender (from_user)
        data = [{
            "userId": str(fr.from_user.userId),
            "name": fr.from_user.name,
            "userName": fr.from_user.userName
        } for fr in incoming_requests]

        return Response(data)
    
from api.models import Article
from api.serializers import ArticleSerializer  # Make sure this includes userId, name, userName

class FriendsLikedArticlesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        friends = user.friends.all()

        # Collect all articles liked by friends
        liked_articles = Article.objects.filter(liked_by_users__in=friends).distinct()

        # You probably need to serialize them
        from api.serializers import ArticleSerializer
        serialized = ArticleSerializer(liked_articles, many=True)
        return Response(serialized.data)
