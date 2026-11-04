# Django already has secure login/logout views, so we use those here.
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    # Public pages and account routes.
    path("", views.article_list, name="article_list"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="news/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Article routes cover the normal CRUD actions.
    path("articles/create/", views.article_create, name="article_create"),
    path("articles/mine/", views.my_articles, name="my_articles"),
    path("articles/<int:pk>/", views.article_detail, name="article_detail"),
    path("articles/<int:pk>/edit/", views.article_update, name="article_update"),
    path("articles/<int:pk>/delete/", views.article_delete, name="article_delete"),
    path(
        "articles/<int:pk>/approve/",
        views.approve_article,
        name="approve_article",
    ),
    path("editor/review/", views.editor_review, name="editor_review"),

    # Newsletter CRUD routes.
    path("newsletters/", views.newsletter_list, name="newsletter_list"),
    path(
        "newsletters/create/",
        views.newsletter_create,
        name="newsletter_create",
    ),
    path(
        "newsletters/<int:pk>/edit/",
        views.newsletter_update,
        name="newsletter_update",
    ),
    path(
        "newsletters/<int:pk>/delete/",
        views.newsletter_delete,
        name="newsletter_delete",
    ),

    # Reader subscription management.
    path("subscriptions/", views.subscriptions, name="subscriptions"),
]
