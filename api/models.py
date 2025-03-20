from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid

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

class User(AbstractBaseUser, PermissionsMixin):
    userId = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    socialMediaId = models.CharField(max_length=255, blank=True, null=True)
    preferredCategories = models.JSONField(default=list)
    location = models.CharField(max_length=255, blank=True, null=True)
    isPremium = models.BooleanField(default=False)
    
    # 🔥 FIX: Remove "api." from ManyToManyField
    likedArticles = models.ManyToManyField(Article, related_name="liked_by_users", blank=True)
    readingHistory = models.ManyToManyField(Article, related_name="reading_history", blank=True)

    friends = models.ManyToManyField("self", blank=True)
    notificationsEnabled = models.BooleanField(default=True)
    privacySettings = models.JSONField(default=dict)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return self.name
