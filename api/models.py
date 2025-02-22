from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    date = models.DateField()
    image = models.ImageField(upload_to='articles/', null=True, blank=True)  # or use `image_path` if it's a string field

    def __str__(self):
        return self.title
