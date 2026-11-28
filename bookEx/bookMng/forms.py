from django import forms
from django.forms import ModelForm
from .models import Book


class BookForm(ModelForm):
    class Meta:
        model = Book
        fields = [
            'name',
            'web',
            'price',
            'picture',
        ]

class BookCommentForm(forms.Form):
    body = forms.CharField(max_length=1000, strip=True)