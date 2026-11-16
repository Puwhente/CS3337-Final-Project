from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from .models import Book, BookComment


class BookCommentsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="reader", password="test-password")
        self.book = Book.objects.create(name="Example Book", web="https://example.com", price="10.00", picture="bookEx/static/uploads/images.jpg", username=self.user)
        self.url = reverse("add_book_comment", args=[self.book.pk])

    def test_visitors_can_read_but_must_log_in_to_post(self):
        BookComment.objects.create(book=self.book, author=self.user, body="A useful book")
        response = self.client.get(reverse("displaybooks"))
        self.assertContains(response, "A useful book")
        self.assertContains(response, "Log in to comment")
        self.assertRedirects(self.client.post(self.url, {"body": "Blocked"}), reverse("login") + "?next=" + self.url)
        self.assertEqual(BookComment.objects.count(), 1)

    def test_post_comment_and_escape_html(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"body": "  <script>alert(1)</script>  "})
        self.assertRedirects(response, reverse("displaybooks") + f"#comments-{self.book.pk}")
        comment = BookComment.objects.get()
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.book, self.book)
        self.assertEqual(comment.body, "<script>alert(1)</script>")
        response = self.client.get(reverse("displaybooks"))
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>")

    def test_reject_blank_and_long_comments(self):
        self.client.force_login(self.user)
        for body in ("   ", "x" * 1001):
            response = self.client.post(self.url, {"body": body})
            self.assertEqual(response.status_code, 400)
        self.assertEqual(BookComment.objects.count(), 0)

    def test_missing_book_and_get_method(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertEqual(self.client.post(reverse("add_book_comment", args=[999999]), {"body": "Hello"}).status_code, 404)

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(self.url, {"body": "Hello"}).status_code, 403)
