import Link from 'next/link';
import { useEffect, useState } from 'react';
import BookCard from '../components/BookCard';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api';
const INITIAL_WEB_IMPORT = { sourceUrl: '', limit: 5 };
const INITIAL_FILE_IMPORT = { title: '', author: '', file: null };

export default function Home() {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [webImport, setWebImport] = useState(INITIAL_WEB_IMPORT);
  const [fileImport, setFileImport] = useState(INITIAL_FILE_IMPORT);
  const [activeImport, setActiveImport] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const [statusError, setStatusError] = useState('');
  const [fileInputKey, setFileInputKey] = useState(0);
  const sampleBookId = books[0]?.id;

  async function fetchBooks({ showSpinner = false } = {}) {
    if (showSpinner) {
      setLoading(true);
    }
    try {
      const res = await fetch(`${API_BASE}/books/`);
      const data = await res.json();
      setBooks(data);
      setError('');
    } catch (err) {
      setError('Unable to load books from backend.');
    } finally {
      if (showSpinner) {
        setLoading(false);
      }
    }
  }

  useEffect(() => {
    fetchBooks({ showSpinner: true });
  }, []);

  async function handleWebImport(event) {
    event.preventDefault();
    setActiveImport('web');
    setStatusMessage('');
    setStatusError('');

    try {
      const res = await fetch(`${API_BASE}/books/upload/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_url: webImport.sourceUrl.trim(),
          limit: Number(webImport.limit) || 5,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Unable to import books from the source.');
      }

      setStatusMessage(`Imported ${data.imported} book${data.imported === 1 ? '' : 's'} from the scraper.`);
      await fetchBooks();
    } catch (err) {
      setStatusError(err.message || 'Unable to import books from the source.');
    } finally {
      setActiveImport('');
    }
  }

  async function handleFileUpload(event) {
    event.preventDefault();
    if (!fileImport.file) {
      setStatusMessage('');
      setStatusError('Choose a .txt, .md, or .html file to upload.');
      return;
    }

    setActiveImport('file');
    setStatusMessage('');
    setStatusError('');

    try {
      const formData = new FormData();
      formData.append('file', fileImport.file);
      formData.append('title', fileImport.title.trim());
      formData.append('author', fileImport.author.trim());

      const res = await fetch(`${API_BASE}/books/upload-file/`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Unable to upload and index the file.');
      }

      const uploadedTitle = data.book?.title || fileImport.file.name;
      setStatusMessage(`Uploaded "${uploadedTitle}" and indexed ${data.chunk_count} text chunk${data.chunk_count === 1 ? '' : 's'}.`);
      setFileImport(INITIAL_FILE_IMPORT);
      setFileInputKey((current) => current + 1);
      await fetchBooks();
    } catch (err) {
      setStatusError(err.message || 'Unable to upload and index the file.');
    } finally {
      setActiveImport('');
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-10 flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-8 shadow-sm sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-sky-600">EgroSphere</p>
            <h1 className="mt-3 text-4xl font-semibold text-slate-900">Book Intelligence Dashboard</h1>
            <p className="mt-3 max-w-2xl text-slate-600">Browse imported books, inspect metadata, upload new text, and ask cited questions over the indexed collection.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link href="/qa" className="rounded-full bg-sky-600 px-5 py-3 text-sm font-semibold text-white hover:bg-sky-700">Ask a question</Link>
            <Link href={sampleBookId ? `/book/${sampleBookId}` : '/qa'} className="rounded-full border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-900 hover:bg-slate-100">Open a book</Link>
          </div>
        </header>

        <section className="mb-8 grid gap-6 xl:grid-cols-2">
          <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm uppercase tracking-[0.24em] text-sky-600">Automation</p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-900">Import from the web</h2>
                <p className="mt-3 max-w-xl text-sm text-slate-600">
                  Trigger the existing scraping pipeline from the frontend. Leave the URL blank to use the default demo source.
                </p>
              </div>
              <span className="rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-sky-700">
                Existing API
              </span>
            </div>

            <form onSubmit={handleWebImport} className="mt-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700">Source URL</label>
                <input
                  type="url"
                  value={webImport.sourceUrl}
                  onChange={(event) => setWebImport((current) => ({ ...current, sourceUrl: event.target.value }))}
                  placeholder="https://books.toscrape.com/"
                  className="mt-2 w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-sky-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700">How many books to import</label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={webImport.limit}
                  onChange={(event) => setWebImport((current) => ({ ...current, limit: event.target.value }))}
                  className="mt-2 w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-sky-500"
                />
              </div>
              <button
                type="submit"
                disabled={activeImport === 'web'}
                className="rounded-full bg-sky-600 px-6 py-3 text-sm font-semibold text-white hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {activeImport === 'web' ? 'Importing...' : 'Import books'}
              </button>
            </form>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm uppercase tracking-[0.24em] text-emerald-600">Local Text</p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-900">Upload a book file</h2>
                <p className="mt-3 max-w-xl text-sm text-slate-600">
                  Upload a plain-text, markdown, or HTML file and the backend will extract readable text, generate insights, and index it for Q&amp;A.
                </p>
              </div>
              <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
                New
              </span>
            </div>

            <form onSubmit={handleFileUpload} className="mt-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700">Book file</label>
                <input
                  key={fileInputKey}
                  type="file"
                  accept=".txt,.md,.html,.htm,text/plain,text/markdown,text/html"
                  onChange={(event) => setFileImport((current) => ({ ...current, file: event.target.files?.[0] || null }))}
                  className="mt-2 block w-full rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-700 file:mr-4 file:rounded-full file:border-0 file:bg-slate-900 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:bg-slate-700"
                />
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-slate-700">Title override (optional)</label>
                  <input
                    type="text"
                    value={fileImport.title}
                    onChange={(event) => setFileImport((current) => ({ ...current, title: event.target.value }))}
                    placeholder="Defaults to the filename"
                    className="mt-2 w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Author (optional)</label>
                  <input
                    type="text"
                    value={fileImport.author}
                    onChange={(event) => setFileImport((current) => ({ ...current, author: event.target.value }))}
                    placeholder="Uploaded file"
                    className="mt-2 w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-emerald-500"
                  />
                </div>
              </div>
              <p className="text-xs text-slate-500">
                Supported formats: <span className="font-semibold text-slate-700">.txt</span>, <span className="font-semibold text-slate-700">.md</span>, <span className="font-semibold text-slate-700">.html</span>, <span className="font-semibold text-slate-700">.htm</span>.
              </p>
              <button
                type="submit"
                disabled={activeImport === 'file'}
                className="rounded-full bg-emerald-600 px-6 py-3 text-sm font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {activeImport === 'file' ? 'Uploading...' : 'Upload and index'}
              </button>
            </form>
          </div>
        </section>

        {(statusMessage || statusError) && (
          <section className="mb-8">
            {statusMessage && (
              <div className="rounded-3xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
                {statusMessage}
              </div>
            )}
            {statusError && (
              <div className="rounded-3xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                {statusError}
              </div>
            )}
          </section>
        )}

        <section className="mb-8 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-slate-900">Available books</h2>
            <p className="text-sm text-slate-500">Loaded from the Django API.</p>
          </div>
          <Link href="/qa" className="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm text-slate-800 hover:bg-slate-100">Go to Q&A</Link>
        </section>

        {loading ? (
          <div className="rounded-3xl border border-slate-200 bg-white p-8 text-center text-slate-500 shadow-sm">Loading books...</div>
        ) : error ? (
          <div className="rounded-3xl border border-red-200 bg-red-50 p-8 text-red-700 shadow-sm">{error}</div>
        ) : books.length === 0 ? (
          <div className="rounded-3xl border border-slate-200 bg-white p-8 text-slate-500 shadow-sm">No books available yet. Use the import controls above to scrape books or upload a local file.</div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {books.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
