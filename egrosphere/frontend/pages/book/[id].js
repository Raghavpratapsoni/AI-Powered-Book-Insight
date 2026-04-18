import { useRouter } from 'next/router';
import Link from 'next/link';
import { useEffect, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api';

export default function BookDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const [book, setBook] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    async function load() {
      try {
        const res = await fetch(`${API_BASE}/books/${id}/`);
        const data = await res.json();
        setBook(data);
        const recRes = await fetch(`${API_BASE}/books/${id}/recommendations/`);
        setRecommendations(await recRes.json());
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex items-center justify-between gap-4">
          <button onClick={() => router.back()} className="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 hover:bg-slate-100">Back</button>
          <h1 className="text-3xl font-semibold text-slate-900">Book detail</h1>
          <Link href="/" className="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700">Dashboard</Link>
        </div>

        {loading ? (
          <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm text-slate-500">Loading book...</div>
        ) : !book ? (
          <div className="rounded-3xl border border-red-200 bg-red-50 p-8 text-red-700 shadow-sm">Book not found.</div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
            <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
              <h2 className="text-3xl font-semibold text-slate-900">{book.title}</h2>
              <p className="mt-2 text-slate-600">Author: {book.author || 'Unknown'}</p>
              <div className="mt-4 rounded-3xl bg-slate-50 p-6 text-slate-700">
                <h3 className="text-lg font-medium text-slate-900">Description</h3>
                <p className="mt-3 whitespace-pre-line text-slate-700">{book.description || 'No description available.'}</p>
              </div>
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
                  <h4 className="text-sm uppercase tracking-[0.2em] text-slate-500">Summary</h4>
                  <p className="mt-2 text-slate-700">{book.summary || 'N/A'}</p>
                </div>
                <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
                  <h4 className="text-sm uppercase tracking-[0.2em] text-slate-500">Genre / Sentiment</h4>
                  <p className="mt-2 text-slate-700">{book.genre || 'N/A'}</p>
                  <p className="text-slate-500">{book.sentiment || 'N/A'}</p>
                </div>
              </div>
            </div>

            <aside className="space-y-6">
              <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-slate-900">Metadata</h3>
                <div className="mt-4 space-y-2 text-slate-600">
                  <p>Rating: {book.rating || 'N/A'}</p>
                  <p>Reviews: {book.reviews_count || 'N/A'}</p>
                  <p>
                    URL:{' '}
                    {book.book_url ? (
                      <a href={book.book_url} target="_blank" rel="noreferrer" className="text-sky-600 hover:text-sky-800">
                        Visit source
                      </a>
                    ) : (
                      <span>Uploaded file</span>
                    )}
                  </p>
                </div>
              </div>
              <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-slate-900">If you like this book, try...</h3>
                <div className="mt-4 space-y-3">
                  {recommendations.length === 0 ? (
                    <p className="text-slate-600">No related books yet.</p>
                  ) : (
                    recommendations.map((item) => (
                      <div key={item.id} className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                        <p className="font-semibold text-slate-900">{item.title}</p>
                        <p className="text-sm text-slate-600">{item.author || 'Unknown'}</p>
                        <Link href={`/book/${item.id}`} className="text-sky-600 hover:text-sky-800 text-sm">View</Link>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </aside>
          </div>
        )}
      </div>
    </div>
  );
}
