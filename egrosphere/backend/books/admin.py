from django.contrib import admin
from .models import Book, BookChunk


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'genre', 'sentiment', 'created_at')
    search_fields = ('title', 'author', 'genre')


@admin.register(BookChunk)
class BookChunkAdmin(admin.ModelAdmin):
    list_display = ('chunk_id', 'book')
    search_fields = ('chunk_id', 'text')
