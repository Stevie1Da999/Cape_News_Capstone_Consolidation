"""Database models for Cape News accounts, stories and newsletters."""

# The custom user model lets us keep the three project roles in one place.
from django.contrib.auth.models import AbstractUser, Group
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    """User account with a role and reader subscriptions."""

    ROLE_CHOICES = [
        ("reader", "Reader"),
        ("editor", "Editor"),
        ("journalist", "Journalist"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="reader",
    )

    # These two fields are mainly used by Reader accounts.
    subscribed_publishers = models.ManyToManyField(
        "Publisher",
        blank=True,
        related_name="subscribers",
    )
    subscribed_journalists = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="journalist_subscribers",
        limit_choices_to={"role": "journalist"},
    )

    def save(self, *args, **kwargs):
        """Save the user and keep their role, group and subscriptions in sync."""

        # Check roles here too, not just on the registration form.
        valid_roles = {choice[0] for choice in self.ROLE_CHOICES}
        if self.role not in valid_roles:
            raise ValidationError({"role": "Please choose a valid user role."})

        super().save(*args, **kwargs)

        # These groups match the roles used in the task.
        role_groups = {
            "reader": "Reader",
            "editor": "Editor",
            "journalist": "Journalist",
        }
        group, _ = Group.objects.get_or_create(name=role_groups[self.role])
        old_groups = Group.objects.filter(name__in=role_groups.values())

        # Keep unrelated groups if an admin has added any.
        self.groups.remove(*old_groups.exclude(pk=group.pk))
        self.groups.add(group)

        # Only Readers can keep subscriptions. ManyToMany fields cannot be
        # set to None, so we remove their saved relationships instead.
        if self.role != "reader":
            self.subscribed_publishers.clear()
            self.subscribed_journalists.clear()

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"


class Publisher(models.Model):
    """News publisher that can have editors and journalists."""

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    editors = models.ManyToManyField(
        User,
        blank=True,
        related_name="edited_publishers",
        limit_choices_to={"role": "editor"},
    )
    journalists = models.ManyToManyField(
        User,
        blank=True,
        related_name="publishers",
        limit_choices_to={"role": "journalist"},
    )

    def __str__(self):
        return self.name


class Article(models.Model):
    """Article written by a journalist and optionally linked to a publisher."""

    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="articles",
        limit_choices_to={"role": "journalist"},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        related_name="articles",
        blank=True,
        null=True,
    )

    def clean(self):
        # A publisher article must be written by one of that publisher's
        # journalists. If there is no publisher, it is an independent article.
        """Check that the author works for the chosen publisher."""

        if (
            self.publisher_id
            and self.author_id
            and not self.publisher.journalists.filter(pk=self.author_id).exists()
        ):
            raise ValidationError(
                "The journalist must belong to the selected publisher."
            )

    def __str__(self):
        return self.title


class Newsletter(models.Model):
    """Collection of approved articles put together by staff."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Editors and journalists can both create newsletters in this project.
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="newsletters",
    )
    articles = models.ManyToManyField(
        Article,
        blank=True,
        related_name="newsletters",
    )

    def __str__(self):
        return self.title


class ApprovalLog(models.Model):
    """Keep a record of an approved article received by our own API."""

    article = models.OneToOneField(
        Article, on_delete=models.CASCADE, related_name="approval_log"
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="approval_logs"
    )
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Approval logged for {self.article.title}"
