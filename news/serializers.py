"""Turn our news models into JSON and check API input."""

# Serializers turn Django model objects into JSON and validate API input.
from rest_framework import serializers

from .models import Article, Newsletter, Publisher, User


class UserSerializer(serializers.ModelSerializer):
    """Small safe version of a user for API responses."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "role"]
        read_only_fields = ["role"]


class PublisherSerializer(serializers.ModelSerializer):
    """Publisher information used by the API."""

    class Meta:
        model = Publisher
        fields = ["id", "name", "description"]


class ArticleSerializer(serializers.ModelSerializer):
    """Article serializer used for list, create and detail endpoints."""

    author = UserSerializer(read_only=True)
    publisher = PublisherSerializer(read_only=True)
    publisher_id = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(),
        source="publisher",
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "content",
            "author",
            "created_at",
            "approved",
            "publisher",
            "publisher_id",
        ]
        read_only_fields = ["created_at"]

    def validate_publisher_id(self, publisher):
        # Journalists may only post under publishers they actually work for.
        """Stop journalists posting stories under the wrong publisher."""

        request = self.context.get("request")
        if (
            request
            and request.user.role == "journalist"
            and publisher
            and not publisher.journalists.filter(pk=request.user.pk).exists()
        ):
            raise serializers.ValidationError(
                "You are not a journalist for this publisher."
            )
        return publisher

    def validate_approved(self, value):
        # Approval is an Editor-only action. Journalists cannot approve their
        # own work by adding approved=true to an API request.
        """Only allow editors to change whether a story is approved."""

        request = self.context.get("request")
        if request and request.user.role != "editor":
            raise serializers.ValidationError(
                "Only editors can change the approval status."
            )
        return value


class NewsletterSerializer(serializers.ModelSerializer):
    """Newsletter serializer required by the project brief."""

    author = UserSerializer(read_only=True)

    class Meta:
        model = Newsletter
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "author",
            "articles",
        ]
