# The admin site is useful for creating Editors, Journalists and Publishers.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Article, ApprovalLog, Newsletter, Publisher, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Show the extra News Application fields in Django admin."""

    fieldsets = UserAdmin.fieldsets + (
        (
            "News Application",
            {
                "fields": (
                    "role",
                    "subscribed_publishers",
                    "subscribed_journalists",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("News Application", {"fields": ("email", "role")}),
    )
    list_display = ("username", "email", "role", "is_staff")
    list_filter = ("role", "is_staff", "is_active")


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Make Publisher relationships easy to set up for testing."""

    list_display = ("name", "description")
    search_fields = ("name",)
    filter_horizontal = ("editors", "journalists")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Show the useful article fields in the admin list."""

    list_display = ("title", "author", "publisher", "approved", "created_at")
    list_filter = ("approved", "publisher", "created_at")
    search_fields = ("title", "author__username", "publisher__name")


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Make newsletters easy to inspect while developing the project."""

    list_display = ("title", "author", "created_at")
    search_fields = ("title", "author__username")
    filter_horizontal = ("articles",)


@admin.register(ApprovalLog)
class ApprovalLogAdmin(admin.ModelAdmin):
    """Let staff inspect the approvals received through the API."""

    list_display = ("article", "approved_by", "received_at")
    readonly_fields = ("article", "approved_by", "received_at")
