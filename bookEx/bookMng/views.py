from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import (
    require_GET,
    require_http_methods,
    require_POST,
)

from .forms import BookForm
from .models import MainMenu, Book, MessageThread, PrivateMessage
from decimal import Decimal


def index(request):
    return render(
        request,
        "bookMng/index.html",
        {
            "item_list": MainMenu.objects.all(),
        },
    )


def postbook(request):
    submitted = False

    if request.method == "POST":
        form = BookForm(request.POST, request.FILES)

        if form.is_valid():
            book = form.save(commit=False)

            try:
                book.username = request.user
            except Exception:
                pass

            book.save()
            return HttpResponseRedirect("/postbook?submitted=True")

    else:
        form = BookForm()

        if "submitted" in request.GET:
            submitted = True

    return render(
        request,
        "bookMng/postbook.html",
        {
            "form": form,
            "item_list": MainMenu.objects.all(),
            "submitted": submitted,
        },
    )


def displaybooks(request):
    selected_filter = request.GET.get("filter", "all")

    if selected_filter not in ("all", "favorites"):
        selected_filter = "all"

    favorite_ids = set()
    books = Book.objects.all()

    if request.user.is_authenticated:
        favorite_ids = set(
            request.user.favorite_books.values_list("id", flat=True)
        )

        if selected_filter == "favorites":
            books = books.filter(favorited_by=request.user)

    elif selected_filter == "favorites":
        books = books.none()

    for book in books:
        if book.picture:
            book.pic_path = book.picture.url[14:]

    return render(
        request,
        "bookMng/displaybooks.html",
        {
            "item_list": MainMenu.objects.all(),
            "books": books,
            "favorite_ids": favorite_ids,
            "selected_filter": selected_filter,
            "is_signed_in": request.user.is_authenticated,
        },
    )


@login_required
@require_POST
def favorite_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    action = request.POST.get("action")

    if action == "add":
        book.favorited_by.add(request.user)

    elif action == "remove":
        book.favorited_by.remove(request.user)

    else:
        return HttpResponse("Invalid favorite action.", status=400)

    selected_filter = request.POST.get("filter", "all")

    if selected_filter not in ("all", "favorites"):
        selected_filter = "all"

    return HttpResponseRedirect(
        str(reverse_lazy("displaybooks")) + "?filter=" + selected_filter
    )


class Register(CreateView):
    template_name = "registration/register.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("register-success")

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.success_url)


def book_detail(request, book_id):
    book = Book.objects.get(id=book_id)
    book.pic_path = book.picture.url[14:]

    return render(
        request,
        "bookMng/book_detail.html",
        {
            "item_list": MainMenu.objects.all(),
            "book": book,
        },
    )


def mybooks(request):
    books = Book.objects.filter(username=request.user)

    for book in books:
        book.pic_path = book.picture.url[14:]

    return render(
        request,
        "bookMng/mybooks.html",
        {
            "item_list": MainMenu.objects.all(),
            "books": books,
        },
    )


def book_delete(request, book_id):
    book = Book.objects.get(id=book_id)
    book.delete()

    return render(
        request,
        "bookMng/book_delete.html",
        {
            "item_list": MainMenu.objects.all(),
        },
    )


User = get_user_model()


@login_required
@require_GET
def inbox(request: HttpRequest) -> HttpResponse:
    threads = (
        MessageThread.objects
        .filter(Q(user1=request.user) | Q(user2=request.user))
        .prefetch_related("messages", "user1", "user2")
        .order_by("-updated_at")
    )

    thread_data = []

    for thread in threads:
        other_user = thread.other_user(request.user)
        latest_message = thread.latest_message()
        unread_count = thread.unread_count_for(request.user)

        thread_data.append(
            {
                "thread": thread,
                "other_user": other_user,
                "latest_message": latest_message,
                "unread_count": unread_count,
            }
        )

    context = {
        "thread_data": thread_data,
    }

    return render(request, "bookMng/inbox.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def thread_detail(request: HttpRequest, thread_id: int) -> HttpResponse:
    thread = get_object_or_404(
        MessageThread.objects.select_related("user1", "user2"),
        pk=thread_id,
    )

    if not thread.has_participant(request.user):
        raise Http404("Message thread not found.")

    if request.method == "POST":
        body = request.POST.get("body", "").strip()

        if not body:
            messages.error(request, "Message body cannot be empty.")
            return redirect("thread_detail", thread_id=thread.id)

        recipient = thread.other_user(request.user)

        PrivateMessage.objects.create(
            thread=thread,
            sender=request.user,
            recipient=recipient,
            body=body,
        )

        thread.save(update_fields=["updated_at"])
        messages.success(request, "Message sent.")

        return redirect("thread_detail", thread_id=thread.id)

    thread_messages = thread.messages.select_related(
        "sender",
        "recipient",
    ).all()

    unread_messages = thread_messages.filter(
        recipient=request.user,
        is_read=False,
    )

    for msg in unread_messages:
        msg.mark_as_read()

    context = {
        "thread": thread,
        "other_user": thread.other_user(request.user),
        "thread_messages": thread_messages,
    }

    return render(request, "bookMng/thread.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def compose_message(request: HttpRequest) -> HttpResponse:
    user_id = request.GET.get("user_id") or request.POST.get("user_id")
    selected_user = None

    if user_id:
        selected_user = get_object_or_404(User, pk=user_id)

        if selected_user == request.user:
            messages.error(request, "You cannot send a message to yourself.")
            return redirect("inbox")

    available_users = User.objects.exclude(
        pk=request.user.pk
    ).order_by("username")

    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        target_user_id = request.POST.get("user_id")

        if not target_user_id:
            messages.error(request, "Please choose a recipient.")

            return render(
                request,
                "bookMng/compose.html",
                {
                    "available_users": available_users,
                    "selected_user": selected_user,
                },
            )

        recipient = get_object_or_404(User, pk=target_user_id)

        if recipient == request.user:
            messages.error(request, "You cannot send a message to yourself.")
            return redirect("compose_message")

        if not body:
            messages.error(request, "Message body cannot be empty.")

            return render(
                request,
                "bookMng/compose.html",
                {
                    "available_users": available_users,
                    "selected_user": recipient,
                },
            )

        thread = MessageThread.get_or_create_thread(
            request.user,
            recipient,
        )

        PrivateMessage.objects.create(
            thread=thread,
            sender=request.user,
            recipient=recipient,
            body=body,
        )

        thread.save(update_fields=["updated_at"])
        messages.success(request, f"Message sent to {recipient.username}.")

        return redirect("thread_detail", thread_id=thread.id)

    context = {
        "available_users": available_users,
        "selected_user": selected_user,
    }

    return render(request, "bookMng/compose.html", context)


@login_required
@require_POST
def mark_thread_read(request: HttpRequest, thread_id: int) -> HttpResponse:
    thread = get_object_or_404(MessageThread, pk=thread_id)

    if not thread.has_participant(request.user):
        raise Http404("Message thread not found.")

    unread_messages = thread.messages.filter(
        recipient=request.user,
        is_read=False,
    )

    for msg in unread_messages:
        msg.mark_as_read()

    messages.success(request, "Thread marked as read.")
    return redirect("thread_detail", thread_id=thread.id)

@login_required
@require_GET
def cart_detail(request):
    book_ids = request.session.get("shopping_cart", [])
    books = list(
        Book.objects.filter(pk__in=book_ids).order_by("name", "pk")
    )

    # Remove deleted listings from the saved cart.
    request.session["shopping_cart"] = [book.pk for book in books]

    total = sum((book.price for book in books), Decimal("0.00"))

    return render(request, "bookMng/cart.html", {
        "item_list": MainMenu.objects.all(),
        "books": books,
        "total": total,
    })

@login_required
@require_POST
def cart_add(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    book_ids = request.session.get("shopping_cart", [])

    if book.pk in book_ids:
        messages.info(request, "This book is already in your cart.")
    else:
        book_ids.append(book.pk)
        request.session["shopping_cart"] = book_ids
        messages.success(request, f"{book.name} was added to your cart.")

    return redirect("cart_detail")

@login_required
@require_POST
def cart_remove(request, book_id):
    request.session["shopping_cart"] = [
        pk
        for pk in request.session.get("shopping_cart", [])
        if pk != book_id
    ]

    return redirect("cart_detail")

def aboutus(request):
    return render(request, "bookMng/aboutus.html", {
        "item_list": MainMenu.objects.all(),
    })