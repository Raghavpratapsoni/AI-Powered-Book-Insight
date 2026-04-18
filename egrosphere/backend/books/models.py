from django.db import models


class Book(models.Model):
    title = models.CharField(max_length=512)
    author = models.CharField(max_length=256, blank=True)
    rating = models.CharField(max_length=64, blank=True)
    reviews_count = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    book_url = models.URLField(max_length=1024, blank=True)
    summary = models.TextField(blank=True)
    genre = models.CharField(max_length=128, blank=True)
    sentiment = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class BookChunk(models.Model):
    book = models.ForeignKey(Book, related_name='chunks', on_delete=models.CASCADE)
    chunk_id = models.CharField(max_length=256, unique=True)
    text = models.TextField()

    def __str__(self):
        return f'Chunk {self.chunk_id[:16]} for {self.book.title}'
