# EgroSphere API Documentation

## Base URL

```text
http://localhost:8000/api
```

## Data Model Summary

### Book

```json
{
  "id": 1,
  "title": "A Light in the Attic",
  "author": "Unknown",
  "rating": "Three",
  "reviews_count": "0",
  "description": "Book description text...",
  "book_url": "https://books.toscrape.com/...",
  "summary": "AI-generated summary...",
  "genre": "Fiction",
  "sentiment": "Positive",
  "created_at": "2026-04-18T12:30:45.123456Z"
}
```

### BookChunk

```json
{
  "chunk_id": "1-0-abc12345",
  "text": "Indexed text chunk..."
}
```

## GET Endpoints

### `GET /books/`

Lists all uploaded or scraped books.

Response:

```json
[
  {
    "id": 1,
    "title": "A Light in the Attic",
    "author": "Unknown",
    "rating": "Three",
    "reviews_count": "0",
    "description": "Book description text...",
    "book_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
    "summary": "AI-generated summary...",
    "genre": "Fiction",
    "sentiment": "Positive",
    "created_at": "2026-04-18T12:30:45.123456Z"
  }
]
```

### `GET /books/<id>/`

Returns the selected book plus its indexed chunks.

Response:

```json
{
  "id": 1,
  "title": "A Light in the Attic",
  "author": "Unknown",
  "rating": "Three",
  "reviews_count": "0",
  "description": "Book description text...",
  "book_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "summary": "AI-generated summary...",
  "genre": "Fiction",
  "sentiment": "Positive",
  "created_at": "2026-04-18T12:30:45.123456Z",
  "chunks": [
    {
      "chunk_id": "1-0-abc12345",
      "text": "Indexed text chunk..."
    }
  ]
}
```

### `GET /books/<id>/recommendations/`

Returns related books ranked by semantic similarity, with genre fallback if vector matches are insufficient.

Response:

```json
[
  {
    "id": 3,
    "title": "Soumission",
    "author": "Unknown",
    "rating": "One",
    "reviews_count": "0",
    "description": "Book description text...",
    "book_url": "https://books.toscrape.com/catalogue/soumission_998/index.html",
    "summary": "AI-generated summary...",
    "genre": "Non-fiction",
    "sentiment": "Neutral",
    "created_at": "2026-04-18T12:35:10.654321Z"
  }
]
```

## POST Endpoints

### `POST /books/upload/`

Scrapes books from the web using Selenium-first automation. For `books.toscrape.com`, the scraper follows pagination and visits detail pages.

Request body:

```json
{
  "source_url": "https://books.toscrape.com/catalogue/page-1.html",
  "limit": 5
}
```

Response:

```json
{
  "imported": 5
}
```

### `POST /books/upload-file/`

Uploads and indexes local book text files. Supported formats are `.txt`, `.md`, `.html`, and `.htm`.

Multipart form fields:

- `file` - required
- `title` - optional override
- `author` - optional override

Response:

```json
{
  "book": {
    "id": 4,
    "title": "Library Mystery",
    "author": "Sample Author",
    "rating": "",
    "reviews_count": "",
    "description": "Preview text...",
    "book_url": "",
    "summary": "Generated summary...",
    "genre": "Fiction",
    "sentiment": "Neutral",
    "created_at": "2026-04-18T13:10:20.123456Z"
  },
  "chunk_count": 5,
  "uploaded_filename": "library-mystery.txt"
}
```

### `POST /qa/`

Runs a RAG query over all indexed books or a single selected book.

Request body:

```json
{
  "question": "What is the main theme of this book?",
  "book_id": 1
}
```

Behavior:

- If `book_id` is provided, retrieval is filtered to that book only.
- If `book_id` is omitted, retrieval searches across all indexed books.
- Responses include source citations and retrieved passages.

Response:

```json
{
  "question": "What is the main theme of this book?",
  "answer": "The book focuses on creativity, playful poetry, and a warm reflective tone. [1]",
  "sources": [
    {
      "source": 1,
      "book_id": 1,
      "title": "A Light in the Attic",
      "chunk_id": "1-0-abc12345"
    }
  ],
  "retrieved_text": [
    "[1] A Light in the Attic - Indexed chunk text..."
  ]
}
```

## Error Format

All API errors use this shape:

```json
{
  "error": "Description of what went wrong"
}
```

Typical status codes:

- `200` - successful GET/QA
- `201` - successful upload/import
- `400` - invalid request payload
- `404` - missing book
- `500` - unexpected processing error

## Example Workflows

### Workflow 1: Scrape, browse, and inspect

```bash
curl -X POST http://localhost:8000/api/books/upload/ ^
  -H "Content-Type: application/json" ^
  -d "{\"source_url\":\"https://books.toscrape.com/catalogue/page-1.html\",\"limit\":5}"

curl http://localhost:8000/api/books/

curl http://localhost:8000/api/books/1/

curl http://localhost:8000/api/books/1/recommendations/
```

### Workflow 2: Upload a local text file and ask a question

```bash
curl -X POST http://localhost:8000/api/books/upload-file/ ^
  -F "file=@samples/books/library-mystery.txt" ^
  -F "author=Sample Author"

curl -X POST http://localhost:8000/api/qa/ ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"What is the central conflict in this book?\",\"book_id\":4}"
```

## Notes

- MySQL is the recommended metadata database for the assessment path.
- SQLite is still supported for quick local experiments.
- LM Studio is supported through its OpenAI-compatible local endpoint.
- LLM responses and embeddings are cached in memory for repeated prompts during development.
