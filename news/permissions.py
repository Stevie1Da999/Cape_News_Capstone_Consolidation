# SAFE_METHODS contains read-only requests such as GET and HEAD.
from rest_framework.permissions import BasePermission, SAFE_METHODS


class ArticlePermission(BasePermission):
    """Apply the Reader, Editor and Journalist rules to article API calls."""

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # All logged-in roles may read articles that their queryset exposes.
        if request.method in SAFE_METHODS:
            return True

        # Only Journalists submit brand-new articles.
        if request.method == "POST":
            return user.role == "journalist"

        # Editors and Journalists can update/delete, with the object rule below
        # making sure Journalists only change their own work.
        if request.method in ["PUT", "PATCH", "DELETE"]:
            return user.role in ["editor", "journalist"]

        return False

    def has_object_permission(self, request, view, obj):
        user = request.user

        if request.method in SAFE_METHODS:
            return True

        if user.role == "editor":
            return True

        if user.role == "journalist":
            return obj.author == user

        return False
