import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions

from .ai import LLMClient
from .utils import clean_text


def build_insights(description: str) -> dict:
    default = {'summary': '', 'genre': '', 'sentiment': ''}
    description = clean_text(description)
    if not description:
        return default

    insights = _build_ai_insights(description)
    if insights['summary'] or insights['genre'] or insights['sentiment']:
        return insights

    summary = description[:240] + '...' if len(description) > 240 else description
    genre = 'Fiction' if re.search(r'novel|story|mystery|love|adventure|poetry', description, re.I) else 'Non-fiction'
    sentiment = 'Positive' if re.search(r'good|excellent|best|amazing|wonderful|uplifting', description, re.I) else 'Neutral'
    return {'summary': summary, 'genre': genre, 'sentiment': sentiment}


def scrape_books_from_site(source_url: str, limit: int = 10) -> list[dict]:
    source_url = source_url.strip() or 'https://books.toscrape.com/'
    limit = max(1, min(int(limit), 25))
    if 'books.toscrape.com' in source_url:
        return _scrape_books_toscrape(source_url, limit)
    return _scrape_generic_books(source_url, limit)


def _build_ai_insights(description: str) -> dict:
    client = LLMClient()
    if not client.enabled:
        return {'summary': '', 'genre': '', 'sentiment': ''}

    system_prompt = (
        'You analyze book descriptions. '
        'Return exactly three lines using this format: '
        'Summary: ...\\nGenre: ...\\nSentiment: ...'
    )
    user_prompt = (
        'Read the following book description and provide a concise summary, the most likely genre, '
        'and the overall sentiment or tone.\n\n'
        f'Description:\n{description}'
    )

    try:
        content = client.chat(
            system_prompt,
            user_prompt,
            max_tokens=220,
            temperature=0.2,
            cache_namespace='book-insights',
        )
    except Exception:
        content = None

    return _parse_structure(content or '')


def _parse_structure(text: str) -> dict:
    data = {'summary': '', 'genre': '', 'sentiment': ''}
    for line in text.splitlines():
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        key = key.strip().lower()
        value = value.strip()
        if key in data:
            data[key] = value
    return data


def _scrape_books_toscrape(start_url: str, limit: int = 10) -> list[dict]:
    books = []
    seen_titles = set()
    driver = _create_driver()
    current_url = start_url

    try:
        while current_url and len(books) < limit:
            page_html = _load_page_source(current_url, driver=driver)
            soup = BeautifulSoup(page_html, 'html.parser')
            article_cards = soup.select('article.product_pod')

            for card in article_cards:
                if len(books) >= limit:
                    break

                anchor = card.select_one('h3 a')
                if not anchor:
                    continue

                title = clean_text(anchor.get('title') or anchor.get_text(' '))
                if not title or title in seen_titles:
                    continue

                relative_link = anchor.get('href', '')
                detail_url = urljoin(current_url, relative_link)
                rating_class = card.select_one('p.star-rating')
                rating = _extract_star_rating(rating_class)
                book_info = _scrape_book_detail(detail_url, driver=driver)
                book_info['title'] = title
                book_info['rating'] = rating
                book_info['book_url'] = detail_url
                books.append(book_info)
                seen_titles.add(title)

            next_link = soup.select_one('li.next a')
            current_url = urljoin(current_url, next_link['href']) if next_link and len(books) < limit else ''
    finally:
        if driver:
            driver.quit()

    return books


def _scrape_generic_books(start_url: str, limit: int = 10) -> list[dict]:
    books = []
    seen_titles = set()
    driver = _create_driver()

    try:
        landing_html = _load_page_source(start_url, driver=driver)
        candidate_urls = _discover_candidate_links(landing_html, start_url, limit * 5)

        if not candidate_urls:
            detail = _extract_generic_book_detail(landing_html, start_url)
            return [detail] if detail else []

        for url in candidate_urls:
            if len(books) >= limit:
                break

            detail_html = _load_page_source(url, driver=driver)
            detail = _extract_generic_book_detail(detail_html, url)
            if not detail:
                continue

            title = detail.get('title', '')
            if not title or title in seen_titles:
                continue

            books.append(detail)
            seen_titles.add(title)
    finally:
        if driver:
            driver.quit()

    return books[:limit]


def _scrape_book_detail(detail_url: str, driver=None) -> dict:
    page_html = _load_page_source(detail_url, driver=driver)
    soup = BeautifulSoup(page_html, 'html.parser')
    description_tag = soup.select_one('#product_description + p')
    description = clean_text(description_tag.get_text(' ')) if description_tag else ''
    author = _extract_author(soup) or 'Unknown'
    review_count = _extract_review_count(soup)
    return {
        'author': author,
        'description': description,
        'reviews_count': review_count,
    }


def _extract_generic_book_detail(page_html: str, page_url: str) -> dict | None:
    soup = BeautifulSoup(page_html, 'html.parser')
    title = (
        _meta_content(soup, 'property', 'og:title')
        or _meta_content(soup, 'name', 'twitter:title')
        or _first_text(soup.select('main h1, article h1, h1'))
        or (clean_text(soup.title.get_text(' ')) if soup.title else '')
    )
    title = clean_text(title)

    description = (
        _meta_content(soup, 'name', 'description')
        or _meta_content(soup, 'property', 'og:description')
        or _longest_paragraph(soup)
    )
    description = clean_text(description)

    if not title or not description:
        return None

    return {
        'title': title,
        'author': _extract_author(soup) or 'Unknown',
        'rating': _extract_rating_text(soup),
        'reviews_count': _extract_review_count(soup),
        'description': description,
        'book_url': page_url,
    }


def _discover_candidate_links(page_html: str, page_url: str, max_links: int) -> list[str]:
    soup = BeautifulSoup(page_html, 'html.parser')
    parsed_base = urlparse(page_url)
    candidates = []
    seen_urls = set()

    for anchor in soup.select('a[href]'):
        absolute_url = urljoin(page_url, anchor.get('href', ''))
        parsed_url = urlparse(absolute_url)
        if parsed_url.scheme not in {'http', 'https'}:
            continue
        if parsed_url.netloc != parsed_base.netloc:
            continue
        if absolute_url in seen_urls:
            continue

        link_text = clean_text(anchor.get_text(' '))
        href = absolute_url.lower()
        score = 0
        if any(keyword in href for keyword in ('book', 'books', 'novel', 'story', 'catalogue', 'product')):
            score += 3
        if any(keyword in link_text.lower() for keyword in ('book', 'details', 'read more', 'novel')):
            score += 2
        if absolute_url.rstrip('/') == page_url.rstrip('/'):
            score -= 10
        if score <= 0:
            continue

        seen_urls.add(absolute_url)
        candidates.append((score, absolute_url))

    candidates.sort(key=lambda item: (-item[0], item[1]))
    return [url for _, url in candidates[:max_links]]


def _create_driver():
    for builder in (_build_edge_driver, _build_chrome_driver):
        try:
            return builder()
        except Exception:
            continue
    return None


def _build_edge_driver():
    options = EdgeOptions()
    options.use_chromium = True
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1600,1200')
    options.add_argument('--log-level=3')
    driver = webdriver.Edge(options=options)
    driver.set_page_load_timeout(20)
    return driver


def _build_chrome_driver():
    options = ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1600,1200')
    options.add_argument('--log-level=3')
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(20)
    return driver


def _load_page_source(url: str, driver=None) -> str:
    if driver:
        try:
            driver.get(url)
            return driver.page_source
        except (TimeoutException, WebDriverException):
            pass

    response = requests.get(url, timeout=20, headers={'User-Agent': 'EgroSphereBot/1.0'})
    response.raise_for_status()
    return response.text


def _extract_author(soup: BeautifulSoup) -> str:
    author_selectors = [
        '[itemprop="author"]',
        'meta[name="author"]',
        '.author',
        '.book-author',
        '.contributor',
    ]
    for selector in author_selectors:
        if selector.startswith('meta'):
            value = _meta_content(soup, 'name', 'author')
            if value:
                return clean_text(value)
            continue

        node = soup.select_one(selector)
        if node:
            text = clean_text(node.get_text(' '))
            if text:
                return text
    return ''


def _extract_review_count(soup: BeautifulSoup) -> str:
    for row in soup.select('table tr'):
        header = clean_text(row.select_one('th').get_text(' ')) if row.select_one('th') else ''
        value = clean_text(row.select_one('td').get_text(' ')) if row.select_one('td') else ''
        if header.lower() in {'number of reviews', 'reviews', 'review count'} and value:
            return value

    text = clean_text(soup.get_text(' '))
    match = re.search(r'(\d[\d,]*)\s+reviews?', text, re.I)
    return match.group(1) if match else ''


def _extract_rating_text(soup: BeautifulSoup) -> str:
    star_node = soup.select_one('.star-rating')
    rating = _extract_star_rating(star_node)
    if rating:
        return rating

    text = clean_text(soup.get_text(' '))
    match = re.search(r'([0-5](?:\.\d)?)\s*(?:/|out of)\s*5', text, re.I)
    return match.group(1) if match else ''


def _extract_star_rating(node) -> str:
    if not node:
        return ''
    classes = node.get('class', [])
    return clean_text(classes[-1]) if classes else ''


def _longest_paragraph(soup: BeautifulSoup) -> str:
    paragraphs = [clean_text(node.get_text(' ')) for node in soup.select('main p, article p, p')]
    paragraphs = [paragraph for paragraph in paragraphs if len(paragraph.split()) >= 12]
    if not paragraphs:
        return ''
    return max(paragraphs, key=len)


def _meta_content(soup: BeautifulSoup, attr_name: str, attr_value: str) -> str:
    node = soup.find('meta', attrs={attr_name: attr_value})
    return clean_text(node.get('content', '')) if node else ''


def _first_text(nodes) -> str:
    for node in nodes:
        text = clean_text(node.get_text(' '))
        if text:
            return text
    return ''
