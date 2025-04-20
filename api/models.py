from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid

# ✅ Move this function OUTSIDE the class
# def generate_unique_guest_username():
#     return f"guest_{uuid.uuid4()}"

class Article(models.Model):
    articleId = models.CharField(max_length=100, unique=True, null=True, blank=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    summary = models.TextField(blank=True, null=True)
    longerSummary = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    tags = models.JSONField(default=list)
    source = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    popularityScore = models.IntegerField(default=0)
    createdAt = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to="articles/", null=True, blank=True)
    priority = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, name, password, **extra_fields)

def generate_unique_guest_username():
    import uuid
    return f"guest_{uuid.uuid4().hex[:10]}"

class User(AbstractBaseUser, PermissionsMixin):
    userId = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    userName = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    socialMediaId = models.CharField(max_length=255, blank=True, null=True)
    preferredCategories = models.JSONField(default=list)
    location = models.CharField(max_length=255, blank=True, null=True)
    isPremium = models.BooleanField(default=False)

    likedArticles = models.ManyToManyField(Article, related_name="liked_by_users", blank=True)
    readingHistory = models.ManyToManyField(Article, related_name="reading_history", blank=True)
    friends = models.ManyToManyField("self", blank=True)
    notificationsEnabled = models.BooleanField(default=True)
    privacySettings = models.JSONField(default=dict)
    
    profilePicture = models.ImageField(upload_to="profile_picture/", null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return self.name

from django.conf import settings

class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
        default='pending'  # ✅ This ensures no migration errors
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user.name} ➡️ {self.to_user.name}"

class ArticleInteraction(models.Model):
    ACTION_CHOICES = [
        ('view', 'Viewed'),
        ('like', 'Liked'),
        ('click', 'Clicked'),
        ('share', 'Shared'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    time_spent = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.userName} - {self.article.title} - {self.action}"

class UserArticleScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    score = models.FloatField()
    priority = models.CharField(max_length=10, choices=[
        ('most', 'Most'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low')
    ])
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'article')

    def __str__(self):
        return f"{self.user.userName} - {self.article.title} - {self.priority} ({self.score:.2f})"
