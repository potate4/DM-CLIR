"""News website crawler"""

from datetime import datetime
from urllib.parse import urljoin
from .base_crawler import BaseCrawler
from ..utils.helpers import generate_doc_id, clean_url, parse_date, count_words


class NewsCrawler(BaseCrawler):
    """Crawler for news websites"""

    def __init__(self, config, language):
        """
        Initialize news crawler

        Args:
            config: Crawler configuration
            language: 'bangla' or 'english'
        """
        super().__init__(config, language)
        self.documents = []
        self.seen_urls = set()

    def crawl_site(self, site_config, target_docs=500):
        """
        Crawl a news site

        Args:
            site_config: Site configuration dict
            target_docs: Target number of documents

        Returns:
            List of document dicts
        """
        site_name = site_config['name']
        base_url = site_config['url']

        self.logger.info(f"Crawling {site_name} (target: {target_docs} docs)")

        # Fetch homepage
        response = self.fetch_page(base_url)
        if not response:
            self.logger.error(f"Failed to fetch homepage: {base_url}")
            return []

        # Extract article links
        soup = self.parse_html(response.content)
        links = self._extract_links(soup, base_url, site_config)

        self.logger.info(f"Found {len(links)} article links")

        # Crawl articles
        collected = 0
        for link in links:
            if collected >= target_docs:
                break

            # Skip if already seen
            clean_link = clean_url(link)
            if clean_link in self.seen_urls:
                continue

            # Parse article
            article = self._parse_article(link, site_config)
            if article:
                self.documents.append(article)
                self.seen_urls.add(clean_link)
                collected += 1

                if collected % 50 == 0:
                    self.logger.info(f"Collected {collected}/{target_docs} documents")

            # Be respectful
            self.add_delay()

        self.logger.info(f"Collected {collected} documents from {site_name}")
        return self.documents

    def _extract_links(self, soup, base_url, site_config):
        """
        Extract article links from page

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for relative links
            site_config: Site configuration

        Returns:
            List of absolute URLs
        """
        links = []
        selector = site_config['selectors'].get('article_links', 'article a')

        for link in soup.select(selector):
            href = link.get('href')
            if href:
                # Convert to absolute URL
                absolute_url = urljoin(base_url, href)
                links.append(absolute_url)

        # Remove duplicates
        return list(set(links))

    def _parse_article(self, url, site_config):
        """
        Parse a single article

        Args:
            url: Article URL
            site_config: Site configuration

        Returns:
            Article dict or None
        """
        response = self.fetch_page(url)
        if not response:
            return None

        soup = self.parse_html(response.content)
        selectors = site_config['selectors']

        try:
            # Extract content
            title = self._extract_title(soup, selectors)
            body = self._extract_body(soup, selectors)
            date = self._extract_date(soup, selectors)

            # Validate
            if not title or len(body) < 100:
                self.logger.debug(f"Skipping (too short): {url}")
                return None

            # Create document
            doc_id = generate_doc_id(url, title)
            word_count = count_words(body)

            article = {
                'doc_id': doc_id,
                'title': title.strip(),
                'body': body.strip(),
                'url': url,
                'date': date,
                'language': self.language,
                'source': site_config['name'],
                'word_count': word_count,
                'crawled_at': datetime.now().isoformat()
            }

            return article

        except Exception as e:
            self.logger.error(f"Error parsing {url}: {str(e)}")
            return None

    def _extract_title(self, soup, selectors):
        """Extract article title"""
        title_selector = selectors.get('title', 'h1')
        title_elem = soup.select_one(title_selector)
        return title_elem.get_text().strip() if title_elem else ""

    def _extract_body(self, soup, selectors):
        """Extract article body"""
        body_selector = selectors.get('body', 'article p')
        paragraphs = soup.select(body_selector)
        body_parts = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
        return ' '.join(body_parts)

    def _extract_date(self, soup, selectors):
        """Extract article date"""
        date_selector = selectors.get('date', 'time')
        date_elem = soup.select_one(date_selector)

        if date_elem:
            # Try datetime attribute first
            date_str = date_elem.get('datetime') or date_elem.get_text()
            return parse_date(date_str)

        # Fallback to current date
        return datetime.now().strftime('%Y-%m-%d')

    def get_documents(self):
        """Get all collected documents"""
        return self.documents

    def get_count(self):
        """Get document count"""
        return len(self.documents)
