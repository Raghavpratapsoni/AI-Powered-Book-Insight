import re
from pathlib import Path

from bs4 import BeautifulSoup


def clean_text(text: str) -> str:
    if not text:
        return ''
    cleaned = re.sub(r'\s+', ' ', text).strip()
    return cleaned


def title_from_filename(filename: str) -> str:
    stem = Path(filename or 'uploaded-book').stem
    normalized = re.sub(r'[-_]+', ' ', stem).strip()
    return normalized.title() or 'Uploaded Book'


def extract_text_from_uploaded_file(uploaded_file) -> dict:
    filename = getattr(uploaded_file, 'name', 'uploaded-book.txt')
    suffix = Path(filename).suffix.lower()
    if suffix not in {'.txt', '.md', '.html', '.htm'}:
        raise ValueError('Supported file types are .txt, .md, .html, and .htm.')

    raw_bytes = uploaded_file.read()
    uploaded_file.seek(0)
    text = _decode_uploaded_bytes(raw_bytes)
    if suffix in {'.html', '.htm'}:
        text = BeautifulSoup(text, 'html.parser').get_text(' ')

    cleaned_text = clean_text(text)
    if not cleaned_text:
        raise ValueError('No readable text could be extracted from the uploaded file.')

    return {
        'filename': filename,
        'title': title_from_filename(filename),
        'text': cleaned_text,
    }


def _decode_uploaded_bytes(raw_bytes: bytes) -> str:
    for encoding in ('utf-8', 'utf-16', 'latin-1'):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode('utf-8', errors='ignore')


def chunk_text(text: str, chunk_size: int = 250, overlap: int = 75) -> list[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return []

    sentences = _split_sentences(cleaned)
    if len(sentences) <= 1:
        return _chunk_by_words(cleaned.split(' '), chunk_size, overlap)

    chunks = []
    current_sentences = []
    current_word_count = 0

    for sentence in sentences:
        sentence_word_count = len(sentence.split())
        if current_sentences and current_word_count + sentence_word_count > chunk_size:
            chunks.append(' '.join(current_sentences).strip())
            current_sentences = _overlap_sentences(current_sentences, overlap)
            current_word_count = sum(len(item.split()) for item in current_sentences)

        current_sentences.append(sentence)
        current_word_count += sentence_word_count

    if current_sentences:
        chunks.append(' '.join(current_sentences).strip())

    return [chunk for chunk in chunks if chunk]


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [part.strip() for part in parts if part.strip()]


def _overlap_sentences(sentences: list[str], overlap_words: int) -> list[str]:
    if overlap_words <= 0:
        return []

    kept = []
    word_total = 0
    for sentence in reversed(sentences):
        kept.insert(0, sentence)
        word_total += len(sentence.split())
        if word_total >= overlap_words:
            break
    return kept


def _chunk_by_words(words: list[str], chunk_size: int, overlap: int) -> list[str]:
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = ' '.join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end == len(words):
            break
        start += max(1, chunk_size - overlap)
    return chunks
