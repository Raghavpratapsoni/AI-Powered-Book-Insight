import { useEffect, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api';

export default function QA() {
  const [question, setQuestion] = useState('What is the theme of the book?');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [bookId, setBookId] = useState('');
  const [books, setBooks] = useState([]);
  const [selectedBook, setSelectedBook] = useState(null);
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    async function fetchBooks() {
      const res = await fetch(`${API_BASE}/books/`);
      setBooks(await res.json());
    }
    fetchBooks();
  }, []);

  useEffect(() => {
    async function fetchBookContext() {
      if (!bookId) {
        setSelectedBook(null);
        setRecommendations([]);
        return;
      }

      try {
        const [bookRes, recommendationRes] = await Promise.all([
          fetch(`${API_BASE}/books/${bookId}/`),
          fetch(`${API_BASE}/books/${bookId}/recommendations/`),
        ]);
        setSelectedBook(await bookRes.json());
        setRecommendations(await recommendationRes.json());
      } catch (err) {
        setSelectedBook(null);
        setRecommendations([]);
      }
    }

    fetchBookContext();
  }, [bookId]);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setResponse(null);
    try {
      const res = await fetch(`${API_BASE}/qa/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, book_id: bookId || null }),
      });
      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setResponse({ answer: 'Unable to reach backend.' });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <h1 className="text-3xl font-semibold text-slate-900">Book Q&A Interface</h1>
          <p className="mt-3 text-slate-600">Ask a question across imported books or choose a specific title to keep retrieval, insights, and recommendations focused on that book.</p>
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">Question</label>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                rows={4}
                className="mt-2 w-full rounded-3xl border border-slate-200 bg-slate-50 p-4 text-slate-900 outline-none focus:border-sky-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Select a book (optional)</label>
              <select
                value={bookId}
                onChange={(e) => setBookId(e.target.value)}
                className="mt-2 w-full rounded-3xl border border-slate-200 bg-slate-50 p-4 text-slate-900 outline-none focus:border-sky-500"
              >
                <option value="">All books</option>
                {books.map((book) => (
                  <option key={book.id} value={book.id}>{book.title}</option>
                ))}
              </select>
            </div>
            <button
              type="submit"
              className="rounded-full bg-sky-600 px-6 py-3 text-sm font-semibold text-white hover:bg-sky-700"
            >
              {loading ? 'Thinking...' : 'Ask question'}
            </button>
          </form>
        </div>

        {selectedBook && (
          <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr_1fr]">
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Summary</p>
              <h2 className="mt-2 text-xl font-semibold text-slate-900">{selectedBook.title}</h2>
              <p className="mt-4 text-slate-700">{selectedBook.summary || 'No AI summary available yet.'}</p>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Genre & Sentiment</p>
              <div className="mt-4 space-y-3 text-slate-700">
                <p>Genre: <span className="font-medium text-slate-900">{selectedBook.genre || 'N/A'}</span></p>
                <p>Sentiment: <span className="font-medium text-slate-900">{selectedBook.sentiment || 'N/A'}</span></p>
                <p>Rating: <span className="font-medium text-slate-900">{selectedBook.rating || 'N/A'}</span></p>
                <p>Reviews: <span className="font-medium text-slate-900">{selectedBook.reviews_count || 'N/A'}</span></p>
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Recommendations</p>
              <div className="mt-4 space-y-3">
                {recommendations.length === 0 ? (
                  <p className="text-slate-600">No related books found yet.</p>
                ) : (
                  recommendations.slice(0, 3).map((book) => (
                    <div key={book.id} className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                      <p className="font-semibold text-slate-900">{book.title}</p>
                      <p className="text-sm text-slate-600">{book.author || 'Unknown'}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {response && (
          <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
            <h2 className="text-2xl font-semibold text-slate-900">Answer</h2>
            <pre className="mt-4 whitespace-pre-wrap text-slate-700">{response.answer || JSON.stringify(response, null, 2)}</pre>
            {response.sources && response.sources.length > 0 && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold text-slate-900">Sources</h3>
                <ul className="mt-3 space-y-2 text-slate-600">
                  {response.sources.map((source) => (
                    <li key={`${source.book_id}-${source.chunk_id}`}>
                      [{source.source}] {source.title}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
