from django.contrib import admin
from .models import Article, User  # Adjust the import if the model is in a different file
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("email", "name", "is_staff", "is_active", "is_superuser")
    list_filter = ("is_staff", "is_active", "is_superuser")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("name", "location", "preferredCategories", "isPremium")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "name", "password1", "password2", "is_staff", "is_active"),
        }),
    )
    search_fields = ("email", "name")
    ordering = ("email",)

admin.site.register(User, CustomUserAdmin)  # ✅ Register User
admin.site.register(Article)  # ✅ Register Article