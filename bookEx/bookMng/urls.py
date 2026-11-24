from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("postbook/", views.postbook, name="postbook"),
    path("displaybooks/", views.displaybooks, name="displaybooks"),

    path(
        "favorite_book/<int:book_id>/",
        views.favorite_book,
        name="favorite_book",
    ),

    path(
        "book_detail/<int:book_id>",
        views.book_detail,
        name="book_detail",
    ),

    path("mybooks/", views.mybooks, name="mybooks"),

    path(
        "book_delete/<int:book_id>",
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
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:book_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:book_id>/', views.cart_remove, name='cart_remove'),
    path('aboutus/', views.aboutus, name='aboutus'),
]