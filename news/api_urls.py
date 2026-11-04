# path connects each API URL to its API view.
from django.urls import path

# Importing the REST API views that we created earlier.
from .api_views import (
    ApprovedArticleAPIView,
    ArticleDetailAPIView,
    ArticleListCreateAPIView,
    SubscribedArticlesAPIView,
)


urlpatterns = [
    # GET returns all approved articles.
    # POST lets a journalist create a new article.
    path(
        "articles/",
        ArticleListCreateAPIView.as_view(),
        name="api_articles",
    ),

    # Returns approved articles from publishers or journalists
    # that the reader has subscribed to.
    path(
        "articles/subscribed/",
        SubscribedArticlesAPIView.as_view(),
        name="api_subscribed_articles",
    ),

    # GET retrieves one article.
    # PUT/PATCH updates it and DELETE removes it if the role is allowed.
    path(
        "articles/<int:pk>/",
        ArticleDetailAPIView.as_view(),
        name="api_article_detail",
    ),

    # Our project will POST here whenever an editor approves an article.
    path(
        "approved/",
        ApprovedArticleAPIView.as_view(),
        name="api_approved",
    ),
]
