import sys
import traceback
from pathlib import Path
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Book
from .serializers import BookSerializer, BookDetailSerializer

# Add parent directory to path for document_engine imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from document_engine.scraper import scrape_books_from_site, build_insights
from document_engine.utils import extract_text_from_uploaded_file
from document_engine.rag import RAGEngine

# Lazy-load RAG engine to avoid loading on startup
_rag_engine = None

def get_rag_engine():
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine


class BookListView(APIView):
    def get(self, request):
        books = Book.objects.order_by('-created_at')
        serialized = BookSerializer(books, many=True)
        return Response(serialized.data)


class BookDetailView(APIView):
    def get(self, request, book_id):
        book = get_object_or_404(Book, pk=book_id)
        serialized = BookDetailSerializer(book)
        return Response(serialized.data)


class BookRecommendationsView(APIView):
    def get(self, request, book_id):
        book = get_object_or_404(Book, pk=book_id)
        related = get_rag_engine().recommend_books(book, limit=5)
        serialized = BookSerializer(related, many=True)
        return Response(serialized.data)


class BookUploadView(APIView):
    def post(self, request):
        source_url = request.data.get('source_url', '')
        limit = int(request.data.get('limit', 10))
        try:
            books_data = scrape_books_from_site(source_url or 'https://books.toscrape.com/', limit=limit)
            created_books = []
            for book_data in books_data:
                book, _ = Book.objects.get_or_create(
                    title=book_data['title'],
                    defaults={
                        'author': book_data.get('author', 'Unknown'),
                        'rating': book_data.get('rating', ''),
                        'reviews_count': book_data.get('reviews_count', ''),
                        'description': book_data.get('description', ''),
                        'book_url': book_data.get('book_url', ''),
                    },
                )
                book.author = book_data.get('author', book.author or 'Unknown')
                book.rating = book_data.get('rating', book.rating or '')
                book.reviews_count = book_data.get('reviews_count', book.reviews_count or '')
                book.description = book_data.get('description', book.description or '')
                book.book_url = book_data.get('book_url', book.book_url or '')
                insights = build_insights(book.description)
                book.summary = insights.get('summary', '')
                book.genre = insights.get('genre', '')
                book.sentiment = insights.get('sentiment', '')
                book.save()

                text_blocks = book.description or book.summary or book.title
                chunks = get_rag_engine().chunk_and_index_book(book, text_blocks)
                created_books.append(book)

            return Response({'imported': len(created_books)}, status=status.HTTP_201_CREATED)
        except Exception as exc:
            traceback.print_exc()
            return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BookFileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({'error': 'A file is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            extracted = extract_text_from_uploaded_file(uploaded_file)
            full_text = extracted['text']
            preview = full_text[:1800] + '...' if len(full_text) > 1800 else full_text
            insight_source = full_text[:4000]
            title = (request.data.get('title') or '').strip() or extracted['title']
            author = (request.data.get('author') or '').strip()

            book = Book.objects.create(
                title=title,
                author=author or 'Uploaded file',
                description=preview,
                book_url='',
            )

            insights = build_insights(insight_source)
            book.summary = insights.get('summary', '')
            book.genre = insights.get('genre', '')
            book.sentiment = insights.get('sentiment', '')
            book.save()

            chunks = get_rag_engine().chunk_and_index_book(book, full_text)
            serialized = BookSerializer(book)
            return Response(
                {
                    'book': serialized.data,
                    'chunk_count': len(chunks),
                    'uploaded_filename': extracted['filename'],
                },
                status=status.HTTP_201_CREATED,
            )
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            traceback.print_exc()
            return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BookQAView(APIView):
    def post(self, request):
        question = request.data.get('question', '')
        book_id = request.data.get('book_id')
        if not question:
            return Response({'error': 'Question text is required.'}, status=status.HTTP_400_BAD_REQUEST)

        context = None
        if book_id:
            book = get_object_or_404(Book, pk=book_id)
            context = f'Book: {book.title}\nDescription: {book.description}'

        try:
            answer = get_rag_engine().answer_question(question, book_id=book_id, context=context)
            return Response(answer)
        except Exception as exc:
            traceback.print_exc()
            return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
