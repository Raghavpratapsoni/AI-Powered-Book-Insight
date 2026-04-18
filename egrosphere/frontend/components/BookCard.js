import Link from 'next/link';

export default function BookCard({ book }) {
  const description = book.description ? `${book.description.slice(0, 180)}${book.description.length > 180 ? '...' : ''}` : 'No description available yet.';
  const summary = book.summary ? `${book.summary.slice(0, 140)}${book.summary.length > 140 ? '...' : ''}` : '';

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">{book.title}</h2>
          <p className="text-sm text-slate-600">Author: {book.author || 'Unknown'}</p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-700">
          {book.genre || 'Unknown genre'}
        </span>
      </div>

      <div className="mt-4 grid gap-3 text-sm text-slate-600 sm:grid-cols-2">
        <p>Rating: <span className="font-medium text-slate-900">{book.rating || 'N/A'}</span></p>
        <p>Reviews: <span className="font-medium text-slate-900">{book.reviews_count || 'N/A'}</span></p>
      </div>

      <div className="mt-4 space-y-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Description</p>
          <p className="mt-2 text-sm text-slate-700">{description}</p>
        </div>
        {summary && (
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">AI Summary</p>
            <p className="mt-2 text-sm text-slate-700">{summary}</p>
          </div>
        )}
      </div>

      <div className="mt-4 flex flex-wrap gap-2 text-sm text-slate-500">
        <span>Sentiment: {book.sentiment || 'N/A'}</span>
      </div>

      <div className="mt-6 flex items-center justify-between">
        <Link href={`/book/${book.id}`} className="rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700">
          View details
        </Link>
        {book.book_url ? (
          <a
            href={book.book_url}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-sky-600 hover:text-sky-800"
          >
            Source URL
          </a>
        ) : (
          <span className="text-sm text-slate-500">Uploaded file</span>
        )}
      </div>
    </div>
  );
}
