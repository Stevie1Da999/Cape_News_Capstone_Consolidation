# requests is used for the required POST to our approved-article API endpoint.
import requests

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core import signing
from django.db.models import Prefetch
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ArticleForm,
    NewsletterForm,
    UserRegistrationForm,
    SubscriptionForm,
)
from .models import Article, ApprovalLog, Newsletter


def article_list(request):
    """Show the public list of approved articles."""

    articles = Article.objects.filter(approved=True).order_by("-created_at")
    return render(request, "news/article_list.html", {"articles": articles})


def article_detail(request, pk):
    """Show one approved article to a normal website visitor."""

    article = get_object_or_404(Article, pk=pk, approved=True)
    return render(request, "news/article_detail.html", {"article": article})


def register(request):
    """Create an account using the role selected on the registration page."""

    if request.user.is_authenticated:
        return redirect("article_list")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the new user in after their selected role has been saved.
            login(request, user)
            return redirect("article_list")
    else:
        form = UserRegistrationForm()

    return render(request, "news/register.html", {"form": form})


@login_required
def article_create(request):
    """Let a Journalist submit an article for Editor approval."""

    if request.user.role != "journalist":
        return HttpResponseForbidden("Only journalists can create articles.")

    if request.method == "POST":
        form = ArticleForm(request.POST, user=request.user)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.approved = False
            article.full_clean()
            article.save()
            return redirect("my_articles")
    else:
        form = ArticleForm(user=request.user)

    return render(
        request,
        "news/article_form.html",
        {"form": form, "page_title": "Write Article"},
    )


@login_required
def my_articles(request):
    """Give Journalists a simple place to manage their own work."""

    if request.user.role != "journalist":
        return HttpResponseForbidden("Only journalists have an article desk.")

    articles = request.user.articles.all().order_by("-created_at")
    return render(request, "news/my_articles.html", {"articles": articles})


@login_required
def article_update(request, pk):
    """Allow an Editor or the article owner to edit an article."""

    article = get_object_or_404(Article, pk=pk)
    allowed = request.user.role == "editor" or (
        request.user.role == "journalist" and article.author == request.user
    )
    if not allowed:
        return HttpResponseForbidden("You cannot edit this article.")

    if request.method == "POST":
        form = ArticleForm(request.POST, instance=article, user=request.user)
        if form.is_valid():
            article = form.save(commit=False)

            # Journalist edits need another Editor review before going public.
            if request.user.role == "journalist":
                article.approved = False

            article.full_clean()
            article.save()
            return redirect(
                "editor_review" if request.user.role == "editor" else "my_articles"
            )
    else:
        form = ArticleForm(instance=article, user=request.user)

    return render(
        request,
        "news/article_form.html",
        {"form": form, "page_title": "Edit Article"},
    )


@login_required
def article_delete(request, pk):
    """Allow Editors or the article owner to delete an article."""

    article = get_object_or_404(Article, pk=pk)
    allowed = request.user.role == "editor" or (
        request.user.role == "journalist" and article.author == request.user
    )
    if not allowed:
        return HttpResponseForbidden("You cannot delete this article.")

    if request.method == "POST":
        article.delete()
        return redirect(
            "editor_review" if request.user.role == "editor" else "my_articles"
        )

    return render(request, "news/article_delete.html", {"article": article})


@login_required
def editor_review(request):
    """Show Editors the articles that are still waiting for approval."""

    if request.user.role != "editor":
        return HttpResponseForbidden("Only editors can review articles.")

    pending_articles = Article.objects.filter(approved=False).order_by("created_at")
    return render(
        request,
        "news/editor_review.html",
        {"pending_articles": pending_articles},
    )


def notify_approved_article(article, request, editor):
    """Email subscribers and POST the approval to our signed internal API."""

    # A set stops duplicate emails if a Reader follows both sources.
    subscriber_emails = set()
    if article.publisher:
        subscriber_emails.update(
            user.email
            for user in article.publisher.subscribers.filter(role="reader")
            if user.email
        )
    subscriber_emails.update(
        user.email
        for user in article.author.journalist_subscribers.filter(role="reader")
        if user.email
    )

    if subscriber_emails:
        send_mail(
            subject=f"New article: {article.title}",
            message=(
                f"{article.title}\n\n{article.content}\n\n"
                f"Written by {article.author.username}."
            ),
            from_email=None,
            recipient_list=sorted(subscriber_emails),
            fail_silently=False,
        )

    # Signing proves this POST came from the approval workflow.
    # The receiving endpoint checks the signature and the database article.
    payload = {"id": article.pk, "editor_id": editor.pk}
    signature = signing.dumps(payload, salt="news-article-approval")
    try:
        response = requests.post(
            request.build_absolute_uri("/api/approved/"),
            json=payload,
            headers={"X-Approval-Signature": signature},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException:
        # Keep a local record even if our own HTTP endpoint is unavailable.
        # The endpoint also saves the record when the POST succeeds.
        ApprovalLog.objects.update_or_create(
            article=article, defaults={"approved_by": editor}
        )


@login_required
def approve_article(request, pk):
    """Approve an article, email subscribers and POST to /api/approved/."""

    if request.user.role != "editor":
        return HttpResponseForbidden("Only editors can approve articles.")

    article = get_object_or_404(Article, pk=pk)

    if request.method == "POST":
        was_approved = article.approved
        article.approved = True
        article.save(update_fields=["approved"])

        if not was_approved:
            notify_approved_article(article, request, request.user)

        return redirect("editor_review")

    return render(request, "news/article_approve.html", {"article": article})


def newsletter_list(request):
    """Show newsletters and the approved articles inside them."""

    newsletters = Newsletter.objects.prefetch_related(
        Prefetch(
            "articles",
            queryset=Article.objects.filter(approved=True),
            to_attr="public_articles",
        )
    ).order_by("-created_at")
    return render(
        request,
        "news/newsletter_list.html",
        {"newsletters": newsletters},
    )


@login_required
def newsletter_create(request):
    """Allow Journalists and Editors to create newsletters."""

    if request.user.role not in ["journalist", "editor"]:
        return HttpResponseForbidden("Readers cannot create newsletters.")

    if request.method == "POST":
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.save()
            form.save_m2m()
            return redirect("newsletter_list")
    else:
        form = NewsletterForm()

    return render(
        request,
        "news/newsletter_form.html",
        {"form": form, "page_title": "Create Newsletter"},
    )


@login_required
def newsletter_update(request, pk):
    """Allow an Editor or newsletter owner to update a newsletter."""

    newsletter = get_object_or_404(Newsletter, pk=pk)
    allowed = request.user.role == "editor" or (
        request.user.role == "journalist" and newsletter.author == request.user
    )
    if not allowed:
        return HttpResponseForbidden("You cannot edit this newsletter.")

    if request.method == "POST":
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            form.save()
            return redirect("newsletter_list")
    else:
        form = NewsletterForm(instance=newsletter)

    return render(
        request,
        "news/newsletter_form.html",
        {"form": form, "page_title": "Edit Newsletter"},
    )


@login_required
def newsletter_delete(request, pk):
    """Allow an Editor or newsletter owner to delete a newsletter."""

    newsletter = get_object_or_404(Newsletter, pk=pk)
    allowed = request.user.role == "editor" or (
        request.user.role == "journalist" and newsletter.author == request.user
    )
    if not allowed:
        return HttpResponseForbidden("You cannot delete this newsletter.")

    if request.method == "POST":
        newsletter.delete()
        return redirect("newsletter_list")

    return render(
        request,
        "news/newsletter_delete.html",
        {"newsletter": newsletter},
    )


@login_required
def subscriptions(request):
    """Let Readers choose the publishers and journalists they follow."""

    if request.user.role != "reader":
        return HttpResponseForbidden("Only readers manage subscriptions.")

    if request.method == "POST":
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            request.user.subscribed_publishers.set(form.cleaned_data["publishers"])
            request.user.subscribed_journalists.set(
                form.cleaned_data["journalists"]
            )
            return redirect("subscriptions")
    else:
        form = SubscriptionForm(
            initial={
                "publishers": request.user.subscribed_publishers.all(),
                "journalists": request.user.subscribed_journalists.all(),
            }
        )

    return render(request, "news/subscriptions.html", {"form": form})
