from django.db import models
from django.utils import timezone

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
    createdAt = models.DateTimeField(null=True, blank=True)  # Make it nullable
    image = models.ImageField(upload_to='articles/', null=True, blank=True)
    priority = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title