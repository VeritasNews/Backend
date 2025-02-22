from django.contrib import admin
from .models import Article  # Adjust the import if the model is in a different file

admin.site.register(Article)
