"""REST API endpoints for articles and editor approvals."""

# Q is useful for the subscribed feed because it needs an OR query.
from django.db.models import Q
from django.core import signing
from django.core.signing import BadSignature, SignatureExpired
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Article, ApprovalLog
from .permissions import ArticlePermission
from .serializers import ArticleSerializer


class ArticleListCreateAPIView(generics.ListCreateAPIView):
    """GET approved articles and POST a new Journalist article."""

    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated, ArticlePermission]

    def get_queryset(self):
        """Only show approved stories in the main API feed."""

        return Article.objects.filter(approved=True).order_by("-created_at")

    def perform_create(self, serializer):
        # Every new article waits for Editor approval.
        """Save a new journalist story as waiting for review."""

        serializer.save(author=self.request.user, approved=False)


class ArticleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """GET one article and allow permitted updates/deletes."""

    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated, ArticlePermission]

    def get_queryset(self):
        """Hide pending stories from readers but let staff see them."""

        user = self.request.user

        # Readers can never open an unapproved article through the API.
        if user.role == "reader":
            return Article.objects.filter(approved=True)

        # Staff roles need unapproved articles for their work.
        return Article.objects.all()

    def perform_update(self, serializer):
        # A Journalist edit sends the article back for approval. An Editor can
        # keep/change approval because approval is part of their role.
        """Save edits and send an approval notice when needed."""

        if self.request.user.role == "journalist":
            serializer.save(approved=False)
        else:
            was_approved = serializer.instance.approved
            article = serializer.save()
            if article.approved and not was_approved:
                # The website and REST API must trigger the same notifications.
                from .views import notify_approved_article
                notify_approved_article(
                    article, self.request, self.request.user
                )


class SubscribedArticlesAPIView(generics.ListAPIView):
    """Return approved articles from a Reader's subscriptions only."""

    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Find approved stories from the publishers and writers I follow."""

        user = self.request.user

        if user.role != "reader":
            return Article.objects.none()

        return (
            Article.objects.filter(approved=True)
            .filter(
                Q(publisher__in=user.subscribed_publishers.all())
                | Q(author__in=user.subscribed_journalists.all())
            )
            .distinct()
            .order_by("-created_at")
        )


class ApprovedArticleAPIView(APIView):
    """Receive and store signed approval messages from our own application."""

    # This is an internal webhook: the signed header is its authentication.
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Check the signed request before recording an approval."""

        signature = request.headers.get("X-Approval-Signature", "")
        try:
            signed_data = signing.loads(
                signature, salt="news-article-approval", max_age=300
            )
        except (BadSignature, SignatureExpired):
            return Response(
                {"error": "Invalid or expired approval signature."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Do not trust arbitrary article IDs or editor names in the JSON body.
        if (
            not isinstance(signed_data, dict)
            or signed_data != dict(request.data)
        ):
            return Response(
                {"error": "Approval details do not match."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        article_id = signed_data.get("id")
        editor_id = signed_data.get("editor_id")
        if (
            type(article_id) is not int or article_id <= 0
            or type(editor_id) is not int or editor_id <= 0
        ):
            return Response(
                {"error": "Invalid article or editor ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        article = Article.objects.filter(
            pk=article_id, approved=True
        ).first()
        if not article:
            return Response(
                {"error": "Approved article not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        from .models import User
        editor = User.objects.filter(
            pk=editor_id, role="editor"
        ).first()
        if editor is None:
            return Response(
                {"error": "An Editor must approve this article."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # update_or_create avoids duplicate log entries when a POST is retried.
        log, created = ApprovalLog.objects.update_or_create(
            article=article, defaults={"approved_by": editor}
        )
        return Response(
            {"message": "Approval logged.", "article_id": article.pk,
             "log_id": log.pk},
            status=(status.HTTP_201_CREATED if created else status.HTTP_200_OK),
        )
