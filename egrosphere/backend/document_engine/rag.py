import hashlib
import sys
import uuid
from pathlib import Path

from django.conf import settings

from .ai import LLMClient
from .utils import chunk_text, clean_text

# Add parent directory to path for books models
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from books.models import Book, BookChunk


class RAGEngine:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        import chromadb

        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        try:
            self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        except Exception:
            self.client = chromadb.Client()

        self.collection = self.client.get_or_create_collection(
            name='book_chunks',
            metadata={'description': 'Book text chunks for retrieval'},
        )
        self.llm = LLMClient()
        self.embedding_cache = {}

    def _embed(self, texts):
        if not texts:
            return []

        cached_vectors = {}
        uncached_texts = []
        uncached_keys = []

        for text in texts:
            normalized = clean_text(text)
            cache_key = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
            if cache_key in self.embedding_cache:
                cached_vectors[cache_key] = self.embedding_cache[cache_key]
            else:
                uncached_texts.append(normalized)
                uncached_keys.append(cache_key)

        if uncached_texts:
            generated = self.model.encode(uncached_texts, convert_to_numpy=True, show_progress_bar=False)
            if hasattr(generated, 'tolist'):
                generated = generated.tolist()
            for cache_key, vector in zip(uncached_keys, generated):
                self.embedding_cache[cache_key] = vector
                cached_vectors[cache_key] = vector

        return [cached_vectors[hashlib.sha256(clean_text(text).encode('utf-8')).hexdigest()] for text in texts]

    def chunk_and_index_book(self, book, text_content, chunk_size=180, overlap=40):
        if not text_content:
            return []

        existing_ids = list(book.chunks.values_list('chunk_id', flat=True))
        if existing_ids:
            try:
                self.collection.delete(ids=existing_ids)
            except Exception:
                pass
            book.chunks.all().delete()

        chunks = chunk_text(text_content, chunk_size=chunk_size, overlap=overlap)
        ids = []
        documents = []
        metadatas = []

        for index, chunk in enumerate(chunks):
            chunk_id = f'{book.id}-{index}-{uuid.uuid4().hex[:8]}'
            BookChunk.objects.create(book=book, chunk_id=chunk_id, text=chunk)
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append(
                {
                    'book_id': int(book.id),
                    'book_title': book.title,
                    'chunk_id': chunk_id,
                }
            )

        if ids:
            embeddings = self._embed(documents)
            self.collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
        return chunks

    def query(self, question, top_k=3, book_id=None, include_distances=False):
        if not question:
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

        include = ['documents', 'metadatas']
        if include_distances:
            include.append('distances')

        try:
            return self.collection.query(
                query_embeddings=self._embed([question]),
                n_results=top_k,
                include=include,
                where={'book_id': int(book_id)} if book_id else None,
            )
        except Exception:
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

    def recommend_books(self, book: Book, limit: int = 5):
        query_text = book.summary or book.description or book.title
        results = self.query(query_text, top_k=max(limit * 6, 12), include_distances=True)
        metadatas = results.get('metadatas', [[]])[0]
        distances = results.get('distances', [[]])[0]

        ranked_ids = []
        scores = {}
        for metadata, distance in zip(metadatas, distances or []):
            candidate_id = metadata.get('book_id')
            if not candidate_id or candidate_id == book.id:
                continue
            if candidate_id not in scores:
                ranked_ids.append(candidate_id)
                scores[candidate_id] = distance if distance is not None else 999
            else:
                scores[candidate_id] = min(scores[candidate_id], distance if distance is not None else scores[candidate_id])

        if ranked_ids:
            books = {item.id: item for item in Book.objects.filter(id__in=ranked_ids)}
            ordered_ids = sorted(ranked_ids, key=lambda candidate_id: scores.get(candidate_id, 999))
            ordered = [books[candidate_id] for candidate_id in ordered_ids if candidate_id in books]
            if ordered:
                return ordered[:limit]

        fallback = Book.objects.exclude(pk=book.pk)
        if book.genre:
            fallback = fallback.filter(genre__icontains=book.genre)
        return list(fallback.order_by('-created_at')[:limit])

    def answer_question(self, question, book_id=None, context=None, top_k=3):
        results = self.query(question, top_k=top_k, book_id=book_id)
        docs = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]

        passages = []
        citations = []
        for index, (doc, metadata) in enumerate(zip(docs, metadatas), start=1):
            citations.append(
                {
                    'source': index,
                    'book_id': metadata.get('book_id'),
                    'title': metadata.get('book_title'),
                    'chunk_id': metadata.get('chunk_id'),
                }
            )
            passages.append(f'[{index}] {metadata.get("book_title")} - {doc}')

        if not passages:
            scope = f' for book ID {book_id}' if book_id else ''
            return {
                'question': question,
                'answer': f'No relevant passages were found{scope}. Try importing more book text or asking a narrower question.',
                'sources': [],
                'retrieved_text': [],
            }

        answer_text = self._generate_answer(question, passages, context=context)
        return {
            'question': question,
            'answer': answer_text,
            'sources': citations,
            'retrieved_text': passages,
        }

    def _generate_answer(self, question: str, passages: list[str], context: str | None = None) -> str:
        if self.llm.enabled:
            system_prompt = (
                'You are a document intelligence assistant for books. '
                'Answer only from the supplied excerpts. '
                'Cite supporting statements with bracketed references like [1] and [2].'
            )
            prompt_parts = []
            if context:
                prompt_parts.append(f'Book context:\n{context}')
            prompt_parts.append('Retrieved excerpts:\n' + '\n\n'.join(passages))
            prompt_parts.append(f'Question: {question}')
            prompt_parts.append('Write a concise answer in 3 to 5 sentences and include citations.')

            try:
                response = self.llm.chat(
                    system_prompt,
                    '\n\n'.join(prompt_parts),
                    max_tokens=320,
                    temperature=0.2,
                    cache_namespace='rag-answer',
                )
                if response:
                    return response
            except Exception:
                pass

        return self._fallback_answer(passages)

    def _fallback_answer(self, passages: list[str]) -> str:
        grounded_points = []
        for passage in passages[:2]:
            label, _, text = passage.partition(' - ')
            snippet = clean_text(text)
            if not snippet:
                continue
            words = snippet.split()
            grounded_points.append(f'{label} {" ".join(words[:28])}{"..." if len(words) > 28 else ""}')

        if grounded_points:
            return 'Based on the retrieved passages, ' + ' '.join(grounded_points)
        return 'No grounded answer could be generated from the retrieved passages.'
