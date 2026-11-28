from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("postbook/", views.postbook, name="postbook"),
    path("displaybooks/", views.displaybooks, name="displaybooks"),
    path("mybooks/", views.mybooks, name="mybooks"),

    path(
        "favorite_book/<int:book_id>/",
        views.favorite_book,
        name="favorite_book",
    ),
    path(
        "book_detail/<int:book_id>/",
        views.book_detail,
        name="book_detail",
    ),
    path(
        "book_delete/<int:book_id>/",
        views.book_delete,
        name="book_delete",
    ),

    path("inbox/", views.inbox, name="inbox"),
    path("compose/", views.compose_message, name="compose_message"),
    path(
        "thread/<int:thread_id>/",
        views.thread_detail,
        name="thread_detail",
    ),
    path(
        "thread/<int:thread_id>/mark-read/",
        views.mark_thread_read,
        name="mark_thread_read",
    ),
    path(
        "books/<int:book_id>/comments/",
        views.add_book_comment,
        name="add_book_comment",
    ),
    path(
        "aboutus/",
        TemplateView.as_view(template_name="bookMng/aboutus.html"),
        name="aboutus",
    ),
]