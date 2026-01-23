"""
Advanced news crawler with multiple strategies.

Strategies:
1. API-based (Prothom Alo) - Uses official JSON API
2. Sitemap-based (Daily Star) - Uses XML sitemaps
3. Cloudscraper (Kaler Kantho, etc.) - Bypasses Cloudflare
4. RSS feed (fallback) - Uses RSS/Atom feeds
5. Archive pages (Dhaka Tribune) - Uses archive URLs
"""

import re
import time
import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Generator
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ..utils.logger import setup_logger
from ..utils.helpers import generate_doc_id, count_words


class AdvancedCrawler:
    """
    Advanced crawler with multiple strategies for different sites.
    """

    def __init__(self, language='english', delay=1.0):
        self.language = language
        self.delay = delay
        self.logger = setup_logger(f'AdvancedCrawler-{language}')
        self.seen_urls = set()
        self.documents = []

        # Setup session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'bn-BD,bn;q=0.9,en;q=0.8' if language == 'bangla' else 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
        })

        # Try to load cloudscraper for Cloudflare bypass
        self._cloudscraper = None
        try:
            import cloudscraper
            self._cloudscraper = cloudscraper.create_scraper(
                browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
            )
            self.logger.info("Cloudscraper available for Cloudflare bypass")
        except ImportError:
            self.logger.warning("cloudscraper not installed. Some sites may fail.")

    def _rate_limit(self):
        """Apply rate limiting"""
        time.sleep(self.delay)

    def _fetch(self, url: str, use_cloudscraper: bool = False) -> Optional[str]:
        """Fetch URL with retry and optional cloudscraper"""
        for attempt in range(3):
            try:
                if use_cloudscraper and self._cloudscraper:
                    response = self._cloudscraper.get(url, timeout=30)
                else:
                    response = self.session.get(url, timeout=30)

                if response.status_code == 200:
                    response.encoding = 'utf-8'
                    return response.text
                elif response.status_code == 403:
                    if not use_cloudscraper and self._cloudscraper:
                        self.logger.info(f"Retrying with cloudscraper: {url}")
                        return self._fetch(url, use_cloudscraper=True)
                    self.logger.warning(f"403 Forbidden: {url}")
                    return None
                else:
                    self.logger.warning(f"HTTP {response.status_code}: {url}")
                    return None
            except Exception as e:
                self.logger.warning(f"Attempt {attempt+1} failed for {url}: {e}")
                time.sleep(2 ** attempt)

        return None

    def _fetch_json(self, url: str, params: dict = None) -> Optional[dict]:
        """Fetch JSON from API"""
        try:
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"API error {url}: {e}")
        return None

    def _load_english_sources(self) -> List[str]:
        """Load English sources for newspaper3k fallback"""
        sources = []
        config_path = Path(__file__).resolve().parents[2] / "config" / "sites.json"
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                for site in data.get("english_sites", []):
                    url = site.get("url")
                    if url:
                        sources.append(url)
            except Exception:
                pass

        sources.append("https://en.prothomalo.com/")
        deduped = []
        for url in sources:
            if url not in deduped:
                deduped.append(url)
        return deduped

    # =========================================================================
    # STRATEGY 1: API-based crawling (Prothom Alo)
    # =========================================================================

    def crawl_prothom_alo_api(self, limit: int = 500) -> int:
        """
        Crawl Prothom Alo using their public API.
        API: https://www.prothomalo.com/api/v1/collections/latest-all
        """
        self.logger.info(f"[Prothom Alo API] Starting (limit: {limit})")

        api_url = "https://www.prothomalo.com/api/v1/collections/latest-all"
        collected = 0
        offset = 0
        batch_size = 50

        while collected < limit:
            params = {"item-type": "story", "offset": offset, "limit": batch_size}
            data = self._fetch_json(api_url, params)

            if not data:
                break

            items = data.get("items", [])
            if not items:
                break

            for item in items:
                if collected >= limit:
                    break

                article = self._parse_prothom_alo_api_item(item, "bangla", "Prothom Alo")
                if article and article['url'] not in self.seen_urls:
                    self.documents.append(article)
                    self.seen_urls.add(article['url'])
                    collected += 1

                    if collected % 50 == 0:
                        self.logger.info(f"[Prothom Alo API] Collected {collected}/{limit}")

            offset += batch_size
            self._rate_limit()

        self.logger.info(f"[Prothom Alo API] Finished: {collected} articles")
        return collected

    def crawl_prothom_alo_en_api(self, limit: int = 500) -> int:
        """
        Crawl Prothom Alo English using their public API.
        API: https://en.prothomalo.com/api/v1/collections/latest-all
        """
        self.logger.info(f"[Prothom Alo EN API] Starting (limit: {limit})")

        api_url = "https://en.prothomalo.com/api/v1/collections/latest-all"
        collected = 0
        offset = 0
        batch_size = 50

        while collected < limit:
            params = {"item-type": "story", "offset": offset, "limit": batch_size}
            data = self._fetch_json(api_url, params)

            if not data:
                break

            items = data.get("items", [])
            if not items:
                break

            for item in items:
                if collected >= limit:
                    break

                article = self._parse_prothom_alo_api_item(item, "english", "Prothom Alo English")
                if article and article['url'] not in self.seen_urls:
                    self.documents.append(article)
                    self.seen_urls.add(article['url'])
                    collected += 1

                    if collected % 50 == 0:
                        self.logger.info(f"[Prothom Alo EN API] Collected {collected}/{limit}")

            offset += batch_size
            self._rate_limit()

        self.logger.info(f"[Prothom Alo EN API] Finished: {collected} articles")
        return collected

    def _parse_prothom_alo_api_item(self, item: dict, language: str, source: str) -> Optional[dict]:
        """Parse article from Prothom Alo API response"""
        try:
            story = item.get("story", {})
            if not story:
                return None

            headline = story.get("headline", "")
            if not headline:
                return None

            url = story.get("url", "")
            if not url:
                slug = story.get("slug", "")
                if slug:
                    url = f"https://www.prothomalo.com/{slug}"
                else:
                    return None

            # Extract body from cards
            body_parts = []
            for card in story.get("cards", []):
                for elem in card.get("story-elements", []):
                    if elem.get("type") == "text":
                        text = re.sub(r"<[^>]+>", "", elem.get("text", ""))
                        if text and len(text) > 20:
                            body_parts.append(text)

            body = "\n\n".join(body_parts)

            # Fallback to summary
            if len(body) < 100:
                body = story.get("summary") or story.get("seo", {}).get("meta-description", "") or body

            if len(body) < 50:
                return None

            # Date
            published_at = story.get("published-at")
            date = None
            if published_at:
                date = datetime.fromtimestamp(published_at / 1000).isoformat()

            return {
                'doc_id': generate_doc_id(url, headline),
                'title': headline,
                'body': body,
                'url': url,
                'date': date,
                'language': language,
                'source': source,
                'word_count': count_words(body),
                'crawled_at': datetime.now().isoformat(),
                'method': 'api'
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None

    # =========================================================================
    # STRATEGY 6: newspaper3k fallback
    # =========================================================================

    def crawl_newspaper3k_sources(self, sources: List[str], limit: int = 500, per_source_limit: int = 400) -> int:
        """Crawl sources using newspaper3k auto-extraction"""
        try:
            import newspaper
        except Exception as e:
            self.logger.error(f"newspaper3k import failed: {e}")
            self.logger.error("Try: pip install newspaper3k lxml_html_clean")
            return 0

        self.logger.info(f"[newspaper3k] Starting (limit: {limit})")
        collected = 0
        if not sources:
            return 0

        per_source = max(per_source_limit, limit // len(sources))
        for source_url in sources:
            if collected >= limit:
                break

            try:
                paper = newspaper.build(source_url, memoize_articles=False)
            except Exception as e:
                self.logger.warning(f"[newspaper3k] Build failed for {source_url}: {e}")
                continue

            count = 0
            for article in paper.articles:
                if collected >= limit or count >= per_source:
                    break
                if not article.url or article.url in self.seen_urls:
                    continue

                try:
                    article.download()
                    article.parse()
                except Exception:
                    continue

                title = (article.title or "").strip()
                body = (article.text or "").strip()
                if len(body) < 100 or not title:
                    continue

                published = article.publish_date
                date = published.isoformat() if published else datetime.now().strftime('%Y-%m-%d')
                source_name = urlparse(source_url).netloc or source_url

                doc = {
                    'doc_id': generate_doc_id(article.url, title),
                    'title': title,
                    'body': body,
                    'url': article.url,
                    'date': date,
                    'language': 'english',
                    'source': source_name,
                    'word_count': count_words(body),
                    'crawled_at': datetime.now().isoformat(),
                    'method': 'newspaper3k'
                }

                self.documents.append(doc)
                self.seen_urls.add(article.url)
                collected += 1
                count += 1

                if collected % 50 == 0:
                    self.logger.info(f"[newspaper3k] Collected {collected}/{limit}")

                self._rate_limit()

        self.logger.info(f"[newspaper3k] Finished: {collected} articles")
        return collected

    # =========================================================================
    # STRATEGY 2: Sitemap-based crawling (Daily Star)
    # =========================================================================

    def crawl_daily_star_sitemap(self, limit: int = 500) -> int:
        """
        Crawl Daily Star using paginated sitemap.
        Sitemap: https://www.thedailystar.net/sitemap.xml?page=N
        Note: Higher page numbers have more recent articles
        """
        self.logger.info(f"[Daily Star Sitemap] Starting (limit: {limit})")

        collected = 0
        max_pages = 30

        # Start from page 50+ for more recent articles (page 1 has old 404 links)
        for page in range(50, 50 + max_pages):
            if collected >= limit:
                break

            sitemap_url = f"https://www.thedailystar.net/sitemap.xml?page={page}"
            xml_content = self._fetch(sitemap_url)

            if not xml_content:
                break

            urls = self._extract_sitemap_urls(xml_content)
            self.logger.info(f"[Daily Star Sitemap] Page {page}: {len(urls)} URLs")

            if not urls:
                break

            for url in urls:
                if collected >= limit:
                    break
                if url in self.seen_urls:
                    continue

                article = self._parse_daily_star_article(url)
                if article:
                    self.documents.append(article)
                    self.seen_urls.add(url)
                    collected += 1

                    if collected % 50 == 0:
                        self.logger.info(f"[Daily Star Sitemap] Collected {collected}/{limit}")

                self._rate_limit()

        self.logger.info(f"[Daily Star Sitemap] Finished: {collected} articles")
        return collected

    def _extract_sitemap_urls(self, xml_content: str) -> List[str]:
        """Extract URLs from sitemap XML"""
        urls = []
        try:
            root = ET.fromstring(xml_content)
            ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            for url_elem in root.findall(".//ns:url/ns:loc", ns):
                if url_elem.text:
                    url = url_elem.text
                    # Only include article URLs (end with numeric ID)
                    if re.search(r'-\d+$', url):
                        urls.append(url)
        except ET.ParseError as e:
            self.logger.error(f"Sitemap parse error: {e}")
        return urls

    def _parse_daily_star_article(self, url: str) -> Optional[dict]:
        """Parse Daily Star article"""
        html = self._fetch(url)
        if not html:
            return None

        try:
            soup = BeautifulSoup(html, "lxml")

            # Title
            title_el = soup.find("h1")
            if not title_el:
                return None
            title = title_el.get_text(strip=True)

            # Body
            body_parts = []
            for selector in [".article-content", "article", ".story-body"]:
                content = soup.select_one(selector)
                if content:
                    for p in content.find_all("p"):
                        text = p.get_text(strip=True)
                        if text and len(text) > 20:
                            body_parts.append(text)
                    break

            body = "\n\n".join(body_parts)
            if len(body) < 100:
                return None

            # Date
            date = None
            date_meta = soup.find("meta", {"property": "article:published_time"})
            if date_meta:
                date = date_meta.get("content")

            return {
                'doc_id': generate_doc_id(url, title),
                'title': title,
                'body': body,
                'url': url,
                'date': date,
                'language': 'english',
                'source': 'The Daily Star',
                'word_count': count_words(body),
                'crawled_at': datetime.now().isoformat(),
                'method': 'sitemap'
            }
        except Exception as e:
            self.logger.debug(f"Parse error {url}: {e}")
            return None

    # =========================================================================
    # STRATEGY 3: Archive page crawling
    # =========================================================================

    def crawl_dhaka_tribune_archive(self, limit: int = 500) -> int:
        """
        Crawl Dhaka Tribune using archive pages.
        Archive: https://www.dhakatribune.com/archive/2024/01/15
        """
        self.logger.info(f"[Dhaka Tribune Archive] Starting (limit: {limit})")

        collected = 0
        from datetime import timedelta

        # Start from today, go backwards
        current_date = datetime.now()
        days_back = 0
        max_days = 365

        while collected < limit and days_back < max_days:
            date = current_date - timedelta(days=days_back)
            archive_url = f"https://www.dhakatribune.com/archive/{date.strftime('%Y/%m/%d')}"

            html = self._fetch(archive_url)
            if html:
                urls = self._extract_archive_urls(html, "https://www.dhakatribune.com")

                for url in urls:
                    if collected >= limit:
                        break
                    if url in self.seen_urls:
                        continue

                    article = self._parse_generic_article(
                        url, 'english', 'Dhaka Tribune',
                        title_selector='h1',
                        body_selector='article p, .article-content p'
                    )
                    if article:
                        self.documents.append(article)
                        self.seen_urls.add(url)
                        collected += 1

                    self._rate_limit()

            days_back += 1

            if days_back % 30 == 0:
                self.logger.info(f"[Dhaka Tribune Archive] {collected} articles from {days_back} days")

        self.logger.info(f"[Dhaka Tribune Archive] Finished: {collected} articles")
        return collected

    def _extract_archive_urls(self, html: str, base_url: str) -> List[str]:
        """Extract article URLs from archive page"""
        urls = []
        soup = BeautifulSoup(html, "lxml")

        for link in soup.find_all("a", href=True):
            href = link["href"]
            # Match article URLs (usually have slugs with numbers)
            if re.search(r'/\d{4,}/', href) or re.search(r'-\d+$', href):
                full_url = urljoin(base_url, href)
                if full_url not in urls:
                    urls.append(full_url)

        return urls[:100]  # Limit per page

    def crawl_newage_archive(self, limit: int = 2500, max_days: int = 730) -> int:
        """
        Crawl New Age using date-based archive pages.
        Archive: https://www.newagebd.net/archive?date=YYYY-MM-DD
        """
        self.logger.info(f"[New Age Archive] Starting (limit: {limit})")

        collected = 0
        from datetime import timedelta

        # Start from today, go backwards
        current_date = datetime.now()
        days_back = 0
        max_days = max_days  # Go back until limit reached or max_days exhausted
        consecutive_zero_days = 0

        while collected < limit and days_back < max_days:
            date = current_date - timedelta(days=days_back)
            date_str = date.strftime("%Y-%m-%d")
            archive_url = f"https://www.newagebd.net/archive?date={date_str}"

            html = self._fetch(archive_url)
            if html:
                urls = self._extract_newage_archive_urls(html)
                self.logger.info(f"[New Age Archive] {date_str}: {len(urls)} articles")
                if not urls:
                    consecutive_zero_days += 1
                else:
                    consecutive_zero_days = 0

                for url in urls:
                    if collected >= limit:
                        break
                    if url in self.seen_urls:
                        continue

                    article = self._parse_newage_article(url)
                    if article:
                        self.documents.append(article)
                        self.seen_urls.add(url)
                        collected += 1

                        if collected % 100 == 0:
                            self.logger.info(f"[New Age Archive] Collected {collected}/{limit}")

                    self._rate_limit()

            if consecutive_zero_days >= 10:
                self.logger.info("[New Age Archive] No links for 10 straight days, switching to categories")
                break

            days_back += 1

            # Progress update every 10 days
            if days_back % 10 == 0:
                self.logger.info(f"[New Age Archive] {collected} articles from {days_back} days")

        self.logger.info(f"[New Age Archive] Finished: {collected} articles")
        return collected

    def crawl_newage_categories(self, limit: int = 2500, max_pages: int = 60) -> int:
        """
        Crawl New Age category listing pages (articlelist).
        Example: https://www.newagebd.net/articlelist/41/bangladesh?page=2
        """
        self.logger.info(f"[New Age Categories] Starting (limit: {limit})")

        categories = [
            (41, "bangladesh"),
            (49, "country"),
            (42, "politics"),
            (47, "foreign-affairs"),
            (31, "world"),
            (29, "business-economy"),
            (22, "sports"),
            (27, "entertainment"),
            (25, "editorial"),
            (12, "science-n-technology"),
        ]

        collected = 0
        for cat_id, slug in categories:
            if collected >= limit:
                break

            empty_pages = 0
            for page in range(1, max_pages + 1):
                if collected >= limit:
                    break

                url = f"https://www.newagebd.net/articlelist/{cat_id}/{slug}"
                if page > 1:
                    url = f"{url}?page={page}"

                html = self._fetch(url)
                if not html:
                    break

                urls = self._extract_newage_articlelist_urls(html)
                if not urls:
                    empty_pages += 1
                    if empty_pages >= 2:
                        break
                    continue

                empty_pages = 0
                for article_url in urls:
                    if collected >= limit:
                        break
                    if article_url in self.seen_urls:
                        continue

                    article = self._parse_newage_article(article_url)
                    if article:
                        self.documents.append(article)
                        self.seen_urls.add(article_url)
                        collected += 1

                        if collected % 100 == 0:
                            self.logger.info(f"[New Age Categories] Collected {collected}/{limit}")

                    self._rate_limit()

        self.logger.info(f"[New Age Categories] Finished: {collected} articles")
        return collected

    def _extract_newage_archive_urls(self, html: str) -> List[str]:
        """Extract article URLs from New Age archive page"""
        urls = []
        soup = BeautifulSoup(html, "lxml")

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "articlelist" in href:
                continue

            if re.search(r"/article/\d+", href) or re.search(r"/post/[^/]+/\d+", href) or re.search(r"/\d{5,}", href):
                full_url = urljoin("https://www.newagebd.net", href)
                if "newagebd.net" in full_url and full_url not in urls:
                    urls.append(full_url)

        return urls

    def _extract_newage_articlelist_urls(self, html: str) -> List[str]:
        """Extract article URLs from New Age category listing pages"""
        urls = []
        soup = BeautifulSoup(html, "lxml")

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "articlelist" in href or "page/" in href:
                continue

            if re.search(r"/post/[^/]+/\d+", href) or re.search(r"/article/\d+", href) or re.search(r"/\d{5,}", href):
                full_url = urljoin("https://www.newagebd.net", href)
                if "newagebd.net" in full_url and full_url not in urls:
                    urls.append(full_url)

        if not urls:
            for script in soup.find_all("script"):
                text = script.string or ""
                for match in re.findall(r"/post/[^/]+/\d+/[a-z0-9-]+", text, re.I):
                    full_url = urljoin("https://www.newagebd.net", match)
                    if full_url not in urls:
                        urls.append(full_url)

        return urls
    def _parse_newage_article(self, url: str) -> Optional[dict]:
        """Parse New Age article"""
        html = self._fetch(url)
        if not html:
            return None

        try:
            soup = BeautifulSoup(html, "lxml")

            # Title
            title_el = soup.find("h1") or soup.select_one(".page-title, .post-title, .article-title")
            if not title_el:
                return None
            title = title_el.get_text(strip=True)

            # Body - try multiple selectors
            body_parts = []
            for selector in [
                ".article-content",
                ".news-content",
                ".content-details",
                ".article-details",
                ".post-details",
                ".details-content",
                "article",
            ]:
                content = soup.select_one(selector)
                if content:
                    for p in content.find_all("p"):
                        text = p.get_text(strip=True)
                        if text and len(text) > 20:
                            body_parts.append(text)
                    break

            # Fallback: get all paragraphs
            if not body_parts:
                for p in soup.find_all("p"):
                    text = p.get_text(strip=True)
                    if text and len(text) > 50:
                        body_parts.append(text)

            body = "\n\n".join(body_parts)
            if len(body) < 100:
                return None

            # Date
            date = None
            date_meta = soup.find("meta", {"property": "article:published_time"})
            if date_meta:
                date = date_meta.get("content")

            # Category
            category = "general"
            cat_el = soup.select_one(".category-name, .news-cat")
            if cat_el:
                category = cat_el.get_text(strip=True).lower()

            return {
                'doc_id': generate_doc_id(url, title),
                'title': title,
                'body': body,
                'url': url,
                'date': date or datetime.now().strftime('%Y-%m-%d'),
                'language': 'english',
                'source': 'New Age',
                'word_count': count_words(body),
                'crawled_at': datetime.now().isoformat(),
                'method': 'archive'
            }
        except Exception as e:
            self.logger.debug(f"Parse error {url}: {e}")
            return None

    # =========================================================================
    # STRATEGY 4: Category page crawling with cloudscraper
    # =========================================================================

    def crawl_kaler_kantho(self, limit: int = 500) -> int:
        """Crawl Kaler Kantho with cloudscraper (Cloudflare protected)"""
        if not self._cloudscraper:
            self.logger.error("cloudscraper required for Kaler Kantho. pip install cloudscraper")
            return 0

        self.logger.info(f"[Kaler Kantho] Starting with cloudscraper (limit: {limit})")

        categories = ["/online/national", "/online/politics", "/online/world",
                     "/online/business", "/online/sports", "/online/entertainment"]
        collected = 0
        per_category = limit // len(categories)

        for category in categories:
            if collected >= limit:
                break

            for page in range(1, 10):
                if collected >= limit:
                    break

                url = f"https://www.kalerkantho.com{category}" + (f"?page={page}" if page > 1 else "")
                html = self._fetch(url, use_cloudscraper=True)

                if not html:
                    break

                article_urls = self._extract_kaler_kantho_urls(html)

                if not article_urls:
                    break

                for article_url in article_urls:
                    if collected >= limit:
                        break
                    if article_url in self.seen_urls:
                        continue

                    article = self._parse_kaler_kantho_article(article_url)
                    if article:
                        self.documents.append(article)
                        self.seen_urls.add(article_url)
                        collected += 1

                    self._rate_limit()

        self.logger.info(f"[Kaler Kantho] Finished: {collected} articles")
        return collected

    def _extract_kaler_kantho_urls(self, html: str) -> List[str]:
        """Extract article URLs from Kaler Kantho"""
        urls = []
        soup = BeautifulSoup(html, "lxml")

        for link in soup.find_all("a", href=True):
            href = link["href"]
            # Match: /online/.../12345
            if re.search(r'/\d{5,}$', href):
                full_url = urljoin("https://www.kalerkantho.com", href)
                if full_url not in urls:
                    urls.append(full_url)

        return urls

    def _parse_kaler_kantho_article(self, url: str) -> Optional[dict]:
        """Parse Kaler Kantho article"""
        html = self._fetch(url, use_cloudscraper=True)
        if not html:
            return None

        try:
            soup = BeautifulSoup(html, "lxml")

            title_el = soup.find("h1")
            if not title_el:
                return None
            title = title_el.get_text(strip=True)

            body_parts = []
            content = soup.find("div", class_=re.compile(r"news-content|article", re.I))
            if content:
                for p in content.find_all("p"):
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        body_parts.append(text)

            body = "\n\n".join(body_parts)
            if len(body) < 50:
                return None

            return {
                'doc_id': generate_doc_id(url, title),
                'title': title,
                'body': body,
                'url': url,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'language': 'bangla',
                'source': 'Kaler Kantho',
                'word_count': count_words(body),
                'crawled_at': datetime.now().isoformat(),
                'method': 'cloudscraper'
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None

    # =========================================================================
    # STRATEGY 5: RSS feed crawling (universal fallback)
    # =========================================================================

    def crawl_rss_feed(self, feed_url: str, source_name: str, limit: int = 100) -> int:
        """Crawl using RSS/Atom feed"""
        self.logger.info(f"[{source_name} RSS] Starting (limit: {limit})")

        xml_content = self._fetch(feed_url)
        if not xml_content:
            return 0

        urls = self._parse_rss_feed(xml_content)
        self.logger.info(f"[{source_name} RSS] Found {len(urls)} entries")

        collected = 0
        for url in urls[:limit]:
            if url in self.seen_urls:
                continue

            article = self._parse_generic_article(
                url,
                self.language,
                source_name,
                title_selector='h1',
                body_selector='article p, .content p, .story-content p'
            )

            if article:
                self.documents.append(article)
                self.seen_urls.add(url)
                collected += 1

            self._rate_limit()

        self.logger.info(f"[{source_name} RSS] Finished: {collected} articles")
        return collected

    def _parse_rss_feed(self, xml_content: str) -> List[str]:
        """Parse RSS/Atom feed for article URLs"""
        urls = []

        # Try feedparser first (handles edge cases better)
        try:
            import feedparser
            feed = feedparser.parse(xml_content)
            for entry in feed.entries:
                url = entry.get('link', '')
                if url:
                    urls.append(url)
            if urls:
                return urls
        except ImportError:
            pass
        except Exception:
            pass

        # Fallback to manual parsing
        try:
            root = ET.fromstring(xml_content)

            # Try RSS format
            for item in root.findall(".//item/link"):
                if item.text:
                    urls.append(item.text.strip())

            # Try Atom format
            if not urls:
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                for link in root.findall(".//atom:entry/atom:link", ns):
                    href = link.get('href')
                    if href:
                        urls.append(href)

        except ET.ParseError as e:
            self.logger.error(f"RSS parse error: {e}")

        return urls

    # =========================================================================
    # Generic article parser
    # =========================================================================

    def _parse_generic_article(self, url: str, language: str, source: str,
                               title_selector: str, body_selector: str) -> Optional[dict]:
        """Generic article parser"""
        html = self._fetch(url)
        if not html:
            return None

        try:
            soup = BeautifulSoup(html, "lxml")

            # Title
            title_el = soup.select_one(title_selector)
            if not title_el:
                return None
            title = title_el.get_text(strip=True)

            # Body
            body_parts = []
            for p in soup.select(body_selector):
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    body_parts.append(text)

            body = "\n\n".join(body_parts)
            if len(body) < 100:
                return None

            # Date
            date = None
            for meta in soup.find_all("meta"):
                if meta.get("property") in ["article:published_time", "og:published_time"]:
                    date = meta.get("content")
                    break

            return {
                'doc_id': generate_doc_id(url, title),
                'title': title,
                'body': body,
                'url': url,
                'date': date or datetime.now().strftime('%Y-%m-%d'),
                'language': language,
                'source': source,
                'word_count': count_words(body),
                'crawled_at': datetime.now().isoformat(),
                'method': 'generic'
            }
        except Exception as e:
            self.logger.debug(f"Parse error {url}: {e}")
            return None

    # =========================================================================
    # High-level crawl methods
    # =========================================================================

    def crawl_bangla(self, total_limit: int = 2500) -> int:
        """Crawl all Bangla sources"""
        per_source = total_limit // 3  # Main 3 sources

        collected = 0

        # 1. Prothom Alo (API - most reliable)
        collected += self.crawl_prothom_alo_api(per_source)

        # 2. Kaler Kantho (cloudscraper)
        collected += self.crawl_kaler_kantho(per_source)

        # 3. RSS feeds for remaining
        rss_sources = [
            ("https://www.banglatribune.com/rss.xml", "Bangla Tribune"),
            ("https://www.dhakapost.com/rss", "Dhaka Post"),
        ]

        remaining = total_limit - collected
        per_rss = remaining // len(rss_sources)

        for feed_url, name in rss_sources:
            collected += self.crawl_rss_feed(feed_url, name, per_rss)

        return collected

    def crawl_english(self, total_limit: int = 2500) -> int:
        """Crawl all English sources"""
        collected = self.crawl_prothom_alo_en_api(total_limit)
        if collected < total_limit:
            remaining = total_limit - collected
            sources = self._load_english_sources()
            collected += self.crawl_newspaper3k_sources(sources, remaining, per_source_limit=400)
        return collected

    def get_documents(self) -> List[dict]:
        """Get all collected documents"""
        return self.documents

    def get_count(self) -> int:
        """Get document count"""
        return len(self.documents)

    def clear(self):
        """Clear collected documents"""
        self.documents = []
        self.seen_urls = set()
