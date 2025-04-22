from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import User
from api.serializers import UserSerializer
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import os

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                'message': 'Registration successful',
                'user_id': user.userId,
                'userName': user.userName,
                'name': user.name,
                'email': user.email,
                'access': access_token,  # Include the access token
                'refresh': str(refresh),  # Include the refresh token
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django.db.models import Q

class LoginView(APIView):
    def post(self, request):
        identifier = request.data.get('identifier')
        password = request.data.get('password')

        user = User.objects.filter(
            Q(email=identifier) | Q(userName=identifier)  # 👈 check either
        ).first()

        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class PasswordResetRequestView(APIView):
    """
    Request a password reset by providing your email address
    """
    def post(self, request):
        email = request.data.get('email', '')
        
        if not email:
            return Response(
                {'error': 'Email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user = User.objects.filter(email=email).first()
        
        if not user:
            # Don't reveal whether a user exists or not for security
            return Response(
                {'success': True, 'message': 'If your email is registered, you will receive a password reset link.'},
                status=status.HTTP_200_OK
            )
        
        # Generate reset token and uid
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create reset link (for mobile deep linking)
        reset_link = f"veritasnews://reset-password/{uid}/{token}"
        # For development on localhost
        fallback_link = f"http://localhost:8000/reset-password/{uid}/{token}"
        
        # Prepare email
        email_subject = "Reset your Veritas News password"
        email_body = render_to_string('password_reset_email.html', {
            'user': user,
            'reset_link': reset_link,
            'fallback_link': fallback_link,
            'uid': uid,
            'token': token,
        })
        
        # If templates directory doesn't exist or template isn't found, use a simple text email instead
        if not os.path.exists(os.path.join(settings.BASE_DIR, 'templates', 'password_reset_email.html')):
            email_body = f"""
            Hello {user.name},
            
            You're receiving this email because you requested a password reset for your Veritas News account.
            
            Please click on the following link to reset your password:
            {reset_link}
            
            If the link doesn't work, copy and paste this URL into your browser:
            {fallback_link}
            
            If you didn't request this, you can safely ignore this email.
            
            Thanks,
            The Veritas News Team
            """
        
        # Send email
        try:
            send_mail(
                email_subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=email_body,
                fail_silently=False
            )
        except Exception as e:
            return Response(
                {'error': f'Error sending email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(
            {'success': True, 'message': 'Password reset email has been sent.'},
            status=status.HTTP_200_OK
        )

class PasswordResetConfirmView(APIView):
    """
    Reset password with token
    """
    def post(self, request):
        uid = request.data.get('uid', '')
        token = request.data.get('token', '')
        new_password = request.data.get('new_password', '')
        
        if not uid or not token or not new_password:
            return Response(
                {'error': 'UID, token, and new password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Validate password
        if len(new_password) < 8:
            return Response(
                {'error': 'Password must be at least 8 characters long'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Decode the user ID
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            
            # Verify token
            if not default_token_generator.check_token(user, token):
                return Response(
                    {'error': 'Invalid or expired token'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Set new password
            user.set_password(new_password)
            user.save()
            
            # Generate new tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True, 
                'message': 'Password has been reset successfully.',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_200_OK)
            
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'error': 'Invalid reset link'},
                status=status.HTTP_400_BAD_REQUEST
            )