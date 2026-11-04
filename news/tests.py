# Automated tests cover both successful actions and blocked actions for roles.
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.core import mail, signing
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Article, ApprovalLog, Newsletter, Publisher, User


class NewsTestDataMixin:
    """Shared test data so each test class uses the same basic setup."""

    def make_data(self):
        self.reader = User.objects.create_user(
            username="reader1",
            email="reader@example.com",
            password="Testpass123!",
            role="reader",
        )
        self.journalist = User.objects.create_user(
            username="journalist1",
            password="Testpass123!",
            role="journalist",
        )
        self.other_journalist = User.objects.create_user(
            username="journalist2",
            password="Testpass123!",
            role="journalist",
        )
        self.editor = User.objects.create_user(
            username="editor1",
            password="Testpass123!",
            role="editor",
        )

        self.publisher = Publisher.objects.create(
            name="Cape City Press",
            description="Local Cape Town stories.",
        )
        self.other_publisher = Publisher.objects.create(name="Other Press")
        self.publisher.journalists.add(self.journalist)
        self.publisher.editors.add(self.editor)
        self.other_publisher.journalists.add(self.other_journalist)

        self.approved_article = Article.objects.create(
            title="Local football returns",
            content="A local football story for testing.",
            author=self.journalist,
            publisher=self.publisher,
            approved=True,
        )
        self.pending_article = Article.objects.create(
            title="Story waiting for review",
            content="This article still needs an editor.",
            author=self.journalist,
            publisher=self.publisher,
            approved=False,
        )
        self.other_article = Article.objects.create(
            title="Unsubscribed story",
            content="This story is from somewhere else.",
            author=self.other_journalist,
            publisher=self.other_publisher,
            approved=True,
        )

        self.newsletter = Newsletter.objects.create(
            title="Weekend Round-up",
            description="Stories worth catching up on.",
            author=self.journalist,
        )
        self.newsletter.articles.add(self.approved_article)


class WebsiteRoleTests(NewsTestDataMixin, TestCase):
    """Test website role permissions, newsletters and approval logic."""

    def setUp(self):
        self.make_data()

    def test_users_are_put_in_the_correct_role_group(self):
        # The post-save signal should keep the role and Django group together.
        self.assertTrue(self.reader.groups.filter(name="Reader").exists())
        self.assertTrue(self.editor.groups.filter(name="Editor").exists())
        self.assertTrue(
            self.journalist.groups.filter(name="Journalist").exists()
        )
        self.assertEqual(Group.objects.filter(name="Reader").count(), 1)

    def test_registration_page_shows_role_choices(self):
        # The registration page must show all three roles from the task.
        response = self.client.get(reverse("register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reader")
        self.assertContains(response, "Journalist")
        self.assertContains(response, "Editor")

    def test_registration_assigns_each_selected_role_and_group(self):
        # Register all three roles and check the saved role and Django Group.
        roles = [
            ("reader", "Reader"),
            ("journalist", "Journalist"),
            ("editor", "Editor"),
        ]

        for role, group_name in roles:
            with self.subTest(role=role):
                username = f"new_{role}"
                response = self.client.post(
                    reverse("register"),
                    {
                        "username": username,
                        "email": f"{username}@example.com",
                        "role": role,
                        "password1": "StrongPass123!",
                        "password2": "StrongPass123!",
                    },
                )

                self.assertEqual(response.status_code, 302)
                user = User.objects.get(username=username)
                self.assertEqual(user.role, role)
                self.assertTrue(user.groups.filter(name=group_name).exists())

                # Registration logs the account in, so log out for the next one.
                self.client.logout()

    def test_model_save_assigns_the_correct_group_after_role_changes(self):
        # This checks User.save(), not just the registration form.
        self.reader.role = "journalist"
        self.reader.save()
        self.reader.refresh_from_db()
        self.assertEqual(self.reader.role, "journalist")
        self.assertTrue(self.reader.groups.filter(name="Journalist").exists())
        self.assertFalse(self.reader.groups.filter(name="Reader").exists())

        self.reader.role = "editor"
        self.reader.save()
        self.assertTrue(self.reader.groups.filter(name="Editor").exists())
        self.assertFalse(self.reader.groups.filter(name="Journalist").exists())

    def test_non_reader_role_clears_both_subscription_lists(self):
        # Reader subscriptions should not stay behind after changing roles.
        self.reader.subscribed_publishers.add(self.publisher)
        self.reader.subscribed_journalists.add(self.journalist)
        self.assertEqual(self.reader.subscribed_publishers.count(), 1)
        self.assertEqual(self.reader.subscribed_journalists.count(), 1)

        self.reader.role = "editor"
        self.reader.save()
        self.assertEqual(self.reader.subscribed_publishers.count(), 0)
        self.assertEqual(self.reader.subscribed_journalists.count(), 0)

    def test_invalid_role_is_not_saved(self):
        from django.core.exceptions import ValidationError

        self.reader.role = "administrator"
        with self.assertRaises(ValidationError):
            self.reader.save()
        self.reader.refresh_from_db()
        self.assertEqual(self.reader.role, "reader")

    def test_groups_have_the_required_article_permissions(self):
        # Check the permissions attached to the role groups after migrations.
        reader = Group.objects.get(name="Reader")
        editor = Group.objects.get(name="Editor")
        journalist = Group.objects.get(name="Journalist")

        self.assertTrue(reader.permissions.filter(codename="view_article").exists())
        self.assertFalse(reader.permissions.filter(codename="add_article").exists())
        self.assertTrue(editor.permissions.filter(codename="change_article").exists())
        self.assertTrue(editor.permissions.filter(codename="delete_article").exists())
        self.assertFalse(editor.permissions.filter(codename="add_article").exists())
        self.assertTrue(journalist.permissions.filter(codename="add_article").exists())

    def test_reader_can_view_articles_and_newsletters(self):
        self.client.force_login(self.reader)
        article_response = self.client.get(reverse("article_list"))
        newsletter_response = self.client.get(reverse("newsletter_list"))
        self.assertEqual(article_response.status_code, 200)
        self.assertContains(article_response, self.approved_article.title)
        self.assertNotContains(article_response, self.pending_article.title)
        self.assertEqual(newsletter_response.status_code, 200)
        self.assertContains(newsletter_response, self.newsletter.title)

    def test_reader_cannot_create_article_or_newsletter(self):
        self.client.force_login(self.reader)
        article_response = self.client.get(reverse("article_create"))
        newsletter_response = self.client.get(reverse("newsletter_create"))
        self.assertEqual(article_response.status_code, 403)
        self.assertEqual(newsletter_response.status_code, 403)

    def test_journalist_can_create_article(self):
        self.client.force_login(self.journalist)
        response = self.client.post(
            reverse("article_create"),
            {
                "title": "New community football story",
                "content": "A new article written for the website.",
                "publisher": self.publisher.pk,
            },
        )
        self.assertEqual(response.status_code, 302)
        article = Article.objects.get(title="New community football story")
        self.assertEqual(article.author, self.journalist)
        self.assertFalse(article.approved)

    def test_journalist_cannot_edit_another_journalists_article(self):
        self.client.force_login(self.journalist)
        response = self.client.get(
            reverse("article_update", args=[self.other_article.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_editor_can_delete_article(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse("article_delete", args=[self.pending_article.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Article.objects.filter(pk=self.pending_article.pk).exists()
        )

    def test_newsletter_can_be_created_and_edited(self):
        self.client.force_login(self.journalist)
        response = self.client.post(
            reverse("newsletter_create"),
            {
                "title": "Football Weekly",
                "description": "This week's football news.",
                "articles": [self.approved_article.pk],
            },
        )
        self.assertEqual(response.status_code, 302)
        newsletter = Newsletter.objects.get(title="Football Weekly")
        self.assertIn(self.approved_article, newsletter.articles.all())

        response = self.client.post(
            reverse("newsletter_update", args=[newsletter.pk]),
            {
                "title": "Football Weekly Updated",
                "description": "Updated description.",
                "articles": [self.approved_article.pk],
            },
        )
        self.assertEqual(response.status_code, 302)
        newsletter.refresh_from_db()
        self.assertEqual(newsletter.title, "Football Weekly Updated")

    @patch("news.views.requests.post")
    def test_editor_approval_emails_subscribers_and_posts_to_api(
        self,
        mock_post,
    ):
        # The Reader follows both sources. They should still receive one email.
        self.reader.subscribed_publishers.add(self.publisher)
        self.reader.subscribed_journalists.add(self.journalist)
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse("approve_article", args=[self.pending_article.pk])
        )
        self.pending_article.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.pending_article.approved)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reader@example.com", mail.outbox[0].to)
        mock_post.assert_called_once()

    def test_non_editor_cannot_approve_article(self):
        self.client.force_login(self.journalist)
        response = self.client.post(
            reverse("approve_article", args=[self.pending_article.pk])
        )
        self.assertEqual(response.status_code, 403)
        self.pending_article.refresh_from_db()
        self.assertFalse(self.pending_article.approved)


class NewsAPITests(NewsTestDataMixin, APITestCase):
    """Test token-authenticated API endpoints and role restrictions."""

    def setUp(self):
        self.make_data()

    def authenticate(self, user):
        # DRF token authentication expects this Authorization header format.
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.get(reverse("api_articles"))
        self.assertIn(response.status_code, [401, 403])

    def test_reader_can_get_approved_articles_only(self):
        self.authenticate(self.reader)
        response = self.client.get(reverse("api_articles"))
        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.data]
        self.assertIn(self.approved_article.title, titles)
        self.assertNotIn(self.pending_article.title, titles)

    def test_reader_only_gets_subscribed_articles(self):
        self.reader.subscribed_publishers.add(self.publisher)
        self.authenticate(self.reader)
        response = self.client.get(reverse("api_subscribed_articles"))
        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.data]
        self.assertIn(self.approved_article.title, titles)
        self.assertNotIn(self.other_article.title, titles)

    def test_reader_cannot_post_article(self):
        self.authenticate(self.reader)
        response = self.client.post(
            reverse("api_articles"),
            {"title": "Reader story", "content": "Not allowed."},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_journalist_can_post_article(self):
        self.authenticate(self.journalist)
        response = self.client.post(
            reverse("api_articles"),
            {
                "title": "API football story",
                "content": "Created through the REST API.",
                "publisher_id": self.publisher.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        article = Article.objects.get(title="API football story")
        self.assertEqual(article.author, self.journalist)
        self.assertFalse(article.approved)

    def test_journalist_cannot_approve_through_api(self):
        self.authenticate(self.journalist)
        response = self.client.patch(
            reverse("api_article_detail", args=[self.pending_article.pk]),
            {"approved": True},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.pending_article.refresh_from_db()
        self.assertFalse(self.pending_article.approved)

    def test_editor_can_approve_through_api(self):
        self.authenticate(self.editor)
        response = self.client.patch(
            reverse("api_article_detail", args=[self.pending_article.pk]),
            {"approved": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.pending_article.refresh_from_db()
        self.assertTrue(self.pending_article.approved)

    def test_journalist_cannot_delete_someone_elses_article(self):
        self.authenticate(self.journalist)
        response = self.client.delete(
            reverse("api_article_detail", args=[self.other_article.pk])
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Article.objects.filter(pk=self.other_article.pk).exists())

    def test_editor_can_delete_article(self):
        self.authenticate(self.editor)
        response = self.client.delete(
            reverse("api_article_detail", args=[self.other_article.pk])
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Article.objects.filter(pk=self.other_article.pk).exists())


class ApprovalRequirementsTests(NewsTestDataMixin, APITestCase):
    """Check the approval rules that are required by the capstone PDF."""

    def setUp(self):
        self.make_data()

    def approval_signature(self, article_id, editor_id):
        return signing.dumps(
            {"id": article_id, "editor_id": editor_id},
            salt="news-article-approval",
        )

    def test_approval_endpoint_rejects_unsigned_requests(self):
        response = self.client.post(
            reverse("api_approved"),
            {"id": self.approved_article.pk, "editor_id": self.editor.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ApprovalLog.objects.count(), 0)

    def test_approval_endpoint_logs_valid_approval_only_once(self):
        payload = {
            "id": self.approved_article.pk, "editor_id": self.editor.pk
        }
        signature = self.approval_signature(
            payload["id"], payload["editor_id"]
        )
        for expected_status in [201, 200]:
            response = self.client.post(
                reverse("api_approved"), payload, format="json",
                HTTP_X_APPROVAL_SIGNATURE=signature,
            )
            self.assertEqual(response.status_code, expected_status)
        self.assertEqual(ApprovalLog.objects.count(), 1)
        self.assertEqual(ApprovalLog.objects.first().approved_by, self.editor)

    def test_approval_endpoint_rejects_pending_article(self):
        payload = {"id": self.pending_article.pk, "editor_id": self.editor.pk}
        response = self.client.post(
            reverse("api_approved"), payload, format="json",
            HTTP_X_APPROVAL_SIGNATURE=self.approval_signature(
                self.pending_article.pk, self.editor.pk
            ),
        )
        self.assertEqual(response.status_code, 404)

    def test_approval_endpoint_rejects_changed_payload(self):
        payload = {"id": self.approved_article.pk, "editor_id": self.editor.pk}
        response = self.client.post(
            reverse("api_approved"),
            {"id": self.pending_article.pk, "editor_id": self.editor.pk},
            format="json",
            HTTP_X_APPROVAL_SIGNATURE=self.approval_signature(
                payload["id"], payload["editor_id"]
            ),
        )
        self.assertEqual(response.status_code, 400)

    @patch("news.views.requests.post")
    def test_editor_api_approval_also_notifies_subscribers(self, mock_post):
        self.reader.subscribed_journalists.add(self.journalist)
        token, _ = Token.objects.get_or_create(user=self.editor)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.patch(
            reverse("api_article_detail", args=[self.pending_article.pk]),
            {"approved": True}, format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        mock_post.assert_called_once()

        # Re-approving should not send a second email.
        response = self.client.patch(
            reverse("api_article_detail", args=[self.pending_article.pk]),
            {"approved": True}, format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        mock_post.assert_called_once()

    def test_newsletter_hides_article_that_is_no_longer_approved(self):
        self.newsletter.articles.add(self.pending_article)
        self.approved_article.approved = False
        self.approved_article.save(update_fields=["approved"])
        response = self.client.get(reverse("newsletter_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.approved_article.title)
        self.assertNotContains(response, self.pending_article.title)

    @patch("news.views.requests.post")
    def test_website_approval_logs_even_if_http_post_fails(self, mock_post):
        import requests

        mock_post.side_effect = requests.RequestException("No local server")
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse("approve_article", args=[self.pending_article.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ApprovalLog.objects.filter(
            article=self.pending_article, approved_by=self.editor
        ).exists())
