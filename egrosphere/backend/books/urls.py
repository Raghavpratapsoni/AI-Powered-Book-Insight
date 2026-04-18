from django.urls import path
from .views import (
    BookListView,
    BookDetailView,
    BookRecommendationsView,
    BookUploadView,
    BookFileUploadView,
    BookQAView,
)

urlpatterns = [
    path('books/', BookListView.as_view(), name='book-list'),
    path('books/<int:book_id>/', BookDetailView.as_view(), name='book-detail'),
    path('books/<int:book_id>/recommendations/', BookRecommendationsView.as_view(), name='book-recommendations'),
    path('books/upload/', BookUploadView.as_view(), name='book-upload'),
    path('books/upload-file/', BookFileUploadView.as_view(), name='book-file-upload'),
    path('qa/', BookQAView.as_view(), name='book-qa'),
]
