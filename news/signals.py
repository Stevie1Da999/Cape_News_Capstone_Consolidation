"""Set up the Reader, Editor and Journalist groups after migrations."""

# This signal creates the role groups and sets up their permissions.
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def create_role_groups(sender, **kwargs):
    """Create role groups and give them the permissions from the brief."""

    if sender.name != "news":
        return

    reader_group, _ = Group.objects.get_or_create(name="Reader")
    editor_group, _ = Group.objects.get_or_create(name="Editor")
    journalist_group, _ = Group.objects.get_or_create(name="Journalist")

    # Filtering by our app avoids accidentally using another app's permission
    # if it happens to have the same codename.
    news_permissions = Permission.objects.filter(content_type__app_label="news")

    reader_group.permissions.set(
        news_permissions.filter(
            codename__in=["view_article", "view_newsletter"]
        )
    )
    editor_group.permissions.set(
        news_permissions.filter(
            codename__in=[
                "view_article",
                "change_article",
                "delete_article",
                "view_newsletter",
                "change_newsletter",
                "delete_newsletter",
            ]
        )
    )
    journalist_group.permissions.set(
        news_permissions.filter(
            codename__in=[
                "add_article",
                "view_article",
                "change_article",
                "delete_article",
                "add_newsletter",
                "view_newsletter",
                "change_newsletter",
                "delete_newsletter",
            ]
        )
    )
