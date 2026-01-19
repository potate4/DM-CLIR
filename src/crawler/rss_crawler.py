"""RSS feed crawler as fallback for blocked sites"""

import feedparser
from datetime import datetime
from .base_crawler import BaseCrawler
from ..utils.helpers import generate_doc_id, count_words


class RSSCrawler(BaseCrawler):
    """Crawl news sites using RSS feeds"""

    def __init__(self, config, language):
        """
        Initialize RSS crawler

        Args:
            config: Crawler configuration
            language: 'bangla' or 'english'
        """
        super().__init__(config, language)
        self.documents = []
        self.seen_urls = set()

    def crawl_feed(self, feed_url, site_name, target_docs=500):
        """
        Crawl RSS feed

        Args:
            feed_url: RSS feed URL
            site_name: Site name
            target_docs: Target documents

        Returns:
            List of documents
        """
        self.logger.info(f"Crawling RSS feed: {feed_url}")

        # Parse feed
        feed = feedparser.parse(feed_url)

        if not feed.entries:
            self.logger.warning(f"No entries found in feed: {feed_url}")
            return []

        self.logger.info(f"Found {len(feed.entries)} entries in RSS feed")

        collected = 0
        for entry in feed.entries:
            if collected >= target_docs:
                break

            # Extract from RSS entry
            article = self._parse_entry(entry, site_name)
            if article:
                # Check if already seen
                if article['url'] not in self.seen_urls:
                    self.documents.append(article)
                    self.seen_urls.add(article['url'])
                    collected += 1

                    if collected % 50 == 0:
                        self.logger.info(f"Collected {collected}/{target_docs} from RSS")

        self.logger.info(f"Collected {collected} documents from RSS feed")
        return self.documents

    def _parse_entry(self, entry, site_name):
        """
        Parse RSS feed entry

        Args:
            entry: feedparser entry
            site_name: Site name

        Returns:
            Document dict or None
        """
        try:
            # Extract basic info from RSS
            title = entry.get('title', '').strip()
            link = entry.get('link', '').strip()

            # Try to get full content
            if hasattr(entry, 'content') and entry.content:
                body = entry.content[0].value
            elif hasattr(entry, 'summary'):
                body = entry.summary
            elif hasattr(entry, 'description'):
                body = entry.description
            else:
                # Fallback: Try to fetch full article
                response = self.fetch_page(link)
                if response:
                    soup = self.parse_html(response.content)
                    # Extract all paragraphs
                    paragraphs = soup.find_all('p')
                    body = ' '.join([p.get_text().strip() for p in paragraphs])
                else:
                    body = ''

            # Clean HTML from body
            from bs4 import BeautifulSoup
            body = BeautifulSoup(body, 'html.parser').get_text()

            # Get date
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                import time
                date = time.strftime('%Y-%m-%d', entry.published_parsed)
            else:
                date = datetime.now().strftime('%Y-%m-%d')

            # Validate
            if not title or len(body) < 100:
                return None

            # Create document
            doc_id = generate_doc_id(link, title)
            word_count = count_words(body)

            article = {
                'doc_id': doc_id,
                'title': title,
                'body': body,
                'url': link,
                'date': date,
                'language': self.language,
                'source': site_name,
                'word_count': word_count,
                'crawled_at': datetime.now().isoformat(),
                'method': 'rss'
            }

            return article

        except Exception as e:
            self.logger.error(f"Error parsing RSS entry: {str(e)}")
            return None

    def get_documents(self):
        """Get collected documents"""
        return self.documents

    def get_count(self):
        """Get document count"""
        return len(self.documents)
