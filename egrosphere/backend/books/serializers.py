from rest_framework import serializers
from .models import Book, BookChunk


class BookChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookChunk
        fields = ['chunk_id', 'text']


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'rating', 'reviews_count', 'description', 'book_url', 'summary', 'genre', 'sentiment', 'created_at']


class BookDetailSerializer(BookSerializer):
    chunks = BookChunkSerializer(many=True, read_only=True)

    class Meta(BookSerializer.Meta):
        fields = BookSerializer.Meta.fields + ['chunks']
