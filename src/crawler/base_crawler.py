"""Base crawler with common functionality"""

import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json

from ..utils.logger import setup_logger
from ..utils.helpers import is_valid_url


class BaseCrawler:
    """Base crawler class with common methods"""

    def __init__(self, config, language):
        """
        Initialize crawler

        Args:
            config: Crawler configuration dict
            language: 'bangla' or 'english'
        """
        self.config = config
        self.language = language
        self.logger = setup_logger(f'Crawler-{language}')

        # Session for persistent connections
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.get('user_agent', 'Mozilla/5.0')
        })

        # Settings
        self.delay = config.get('delay_between_requests', 2)
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)

    def fetch_page(self, url, retries=0):
        """
        Fetch a webpage with retry logic

        Args:
            url: URL to fetch
            retries: Current retry count

        Returns:
            Response object or None
        """
        if not is_valid_url(url):
            self.logger.warning(f"Invalid URL: {url}")
            return None

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response

        except requests.RequestException as e:
            if retries < self.max_retries:
                wait_time = 2 ** retries  # Exponential backoff
                self.logger.warning(f"Retry {retries + 1}/{self.max_retries} for {url} in {wait_time}s")
                time.sleep(wait_time)
                return self.fetch_page(url, retries + 1)
            else:
                self.logger.error(f"Failed to fetch {url}: {str(e)}")
                return None

    def parse_html(self, html_content):
        """
        Parse HTML with BeautifulSoup

        Args:
            html_content: HTML string or bytes

        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html_content, 'lxml')

    def add_delay(self):
        """Add delay between requests"""
        time.sleep(self.delay)

    def save_json(self, data, filepath):
        """
        Save data as JSON

        Args:
            data: Data to save
            filepath: Path to save file
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.logger.debug(f"Saved to {filepath}")
