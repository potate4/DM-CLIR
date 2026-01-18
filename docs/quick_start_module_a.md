# Quick Start Guide: Module A Implementation

This guide will help you get started with implementing Module A (Dataset Construction & Indexing).

## Prerequisites

1. Python 3.8+ installed
2. Virtual environment activated
3. Git repository initialized

## Step-by-Step Implementation

### Step 1: Environment Setup

```bash
# Navigate to project directory
cd DM-CLIR

# Activate virtual environment
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Download NLP models
python -m spacy download en_core_web_sm
python -m spacy download xx_ent_wiki_sm
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"
```

### Step 2: Implement Base Crawler

Create `src/crawler/base_crawler.py`:

```python
import requests
import time
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
from pathlib import Path

class BaseCrawler:
    """Base crawler with common functionality"""

    def __init__(self, config, language):
        self.config = config
        self.language = language
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.get('user_agent', 'Mozilla/5.0')
        })
        self.delay = config.get('delay_between_requests', 2)
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.logger = logging.getLogger(self.__class__.__name__)

    def fetch_page(self, url, retries=0):
        """Fetch a webpage with retry logic"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if retries < self.max_retries:
                wait_time = 2 ** retries  # Exponential backoff
                self.logger.warning(f"Failed to fetch {url}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                return self.fetch_page(url, retries + 1)
            else:
                self.logger.error(f"Failed to fetch {url} after {self.max_retries} retries: {e}")
                return None

    def parse_html(self, html_content):
        """Parse HTML content with BeautifulSoup"""
        return BeautifulSoup(html_content, 'lxml')

    def add_delay(self):
        """Add delay between requests"""
        time.sleep(self.delay)

    def save_raw_data(self, data, filename):
        """Save raw data to JSON file"""
        filepath = Path(f"data/raw/{self.language}/{filename}")
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Saved data to {filepath}")
```

**Test it**:
```bash
python -c "from src.crawler.base_crawler import BaseCrawler; print('BaseCrawler imported successfully!')"
```

### Step 3: Implement News Crawler

Create `src/crawler/news_crawler.py`:

```python
from .base_crawler import BaseCrawler
from datetime import datetime
import re

class NewsCrawler(BaseCrawler):
    """Crawler for news websites"""

    def __init__(self, config, language):
        super().__init__(config, language)
        self.documents = []
        self.doc_count = 0

    def crawl_site(self, site_config, target_docs=500):
        """Crawl a single news site"""
        self.logger.info(f"Starting crawl of {site_config['name']}")

        base_url = site_config['url']
        homepage = self.fetch_page(base_url)

        if not homepage:
            self.logger.error(f"Failed to fetch homepage: {base_url}")
            return []

        soup = self.parse_html(homepage.content)
        article_links = self.extract_article_links(soup, site_config['selectors'])

        self.logger.info(f"Found {len(article_links)} article links")

        for link in article_links[:target_docs]:
            if self.doc_count >= target_docs:
                break

            article = self.parse_article(link, site_config)
            if article:
                self.documents.append(article)
                self.doc_count += 1

                # Save periodically
                if self.doc_count % 100 == 0:
                    self.save_progress()

            self.add_delay()

        self.logger.info(f"Crawled {self.doc_count} documents from {site_config['name']}")
        return self.documents

    def extract_article_links(self, soup, selectors):
        """Extract article links from page"""
        links = []
        link_selector = selectors.get('article_links', 'article a')

        for link in soup.select(link_selector):
            href = link.get('href')
            if href:
                # Convert relative URLs to absolute
                full_url = urljoin(self.config['base_url'], href)
                links.append(full_url)

        # Remove duplicates
        return list(set(links))

    def parse_article(self, url, site_config):
        """Parse a single article"""
        self.logger.debug(f"Parsing article: {url}")

        response = self.fetch_page(url)
        if not response:
            return None

        soup = self.parse_html(response.content)
        selectors = site_config['selectors']

        try:
            title = self.extract_title(soup, selectors)
            body = self.extract_body(soup, selectors)
            date = self.extract_date(soup, selectors)

            # Validation
            if not title or len(body) < 100:
                self.logger.warning(f"Skipping article with insufficient content: {url}")
                return None

            article = {
                'doc_id': f"{site_config['name'].replace(' ', '_')}_{self.doc_count:05d}",
                'title': title,
                'body': body,
                'url': url,
                'date': date,
                'language': self.language,
                'source': site_config['name'],
                'crawled_at': datetime.now().isoformat()
            }

            return article

        except Exception as e:
            self.logger.error(f"Error parsing article {url}: {e}")
            return None

    def extract_title(self, soup, selectors):
        """Extract article title"""
        title_elem = soup.select_one(selectors.get('title', 'h1'))
        return title_elem.get_text().strip() if title_elem else ""

    def extract_body(self, soup, selectors):
        """Extract article body"""
        body_elems = soup.select(selectors.get('body', 'article p'))
        body_parts = [elem.get_text().strip() for elem in body_elems]
        return ' '.join(body_parts)

    def extract_date(self, soup, selectors):
        """Extract article date"""
        date_elem = soup.select_one(selectors.get('date', 'time'))
        if date_elem:
            date_str = date_elem.get('datetime') or date_elem.get_text()
            # Basic date parsing (can be improved)
            return date_str.strip()
        return datetime.now().strftime('%Y-%m-%d')

    def save_progress(self):
        """Save current progress"""
        filename = f"progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.save_raw_data({
            'documents': self.documents,
            'count': self.doc_count
        }, filename)
```

### Step 4: Create Crawler Script

Create `scripts/run_crawler.py`:

```python
import argparse
import yaml
import json
import logging
from pathlib import Path
from src.crawler.news_crawler import NewsCrawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_config(config_path):
    """Load crawler configuration"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_sites(sites_path):
    """Load sites configuration"""
    with open(sites_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description='Run news crawler')
    parser.add_argument('--language', choices=['bangla', 'english', 'both'],
                        default='both', help='Language to crawl')
    parser.add_argument('--target', type=int, default=2500,
                        help='Target documents per language')
    parser.add_argument('--sites', type=str,
                        help='Specific sites to crawl (comma-separated)')

    args = parser.parse_args()

    # Load configurations
    config = load_config('config/crawler_config.yaml')
    sites_config = load_sites('config/sites.json')

    languages = ['bangla', 'english'] if args.language == 'both' else [args.language]

    for language in languages:
        print(f"\n{'='*60}")
        print(f"Crawling {language.upper()} documents")
        print(f"{'='*60}\n")

        sites_key = f"{language}_sites"
        sites = sites_config[sites_key]

        # Filter specific sites if requested
        if args.sites:
            site_names = [s.strip() for s in args.sites.split(',')]
            sites = [s for s in sites if s['name'] in site_names]

        docs_per_site = args.target // len(sites)

        crawler = NewsCrawler(config['crawler'], language)

        for site in sites:
            print(f"\nCrawling: {site['name']}")
            print(f"Target: {docs_per_site} documents")

            try:
                documents = crawler.crawl_site(site, docs_per_site)
                print(f"✓ Collected {len(documents)} documents\n")
            except Exception as e:
                print(f"✗ Error crawling {site['name']}: {e}\n")

        # Save final results
        output_path = Path(f"data/processed/{language}_docs.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for doc in crawler.documents:
                f.write(json.dumps(doc, ensure_ascii=False) + '\n')

        print(f"\n✓ Saved {len(crawler.documents)} documents to {output_path}")

if __name__ == '__main__':
    main()
```

### Step 5: Test the Crawler

```bash
# Test with a small sample first
python scripts/run_crawler.py --language english --target 10

# Check the output
cat data/processed/english_docs.json
```

### Step 6: Implement Text Preprocessing

Create `src/preprocessing/text_cleaner.py`:

```python
import re
import unicodedata

class TextCleaner:
    """Clean and normalize text"""

    def __init__(self, language):
        self.language = language

    def clean(self, text):
        """Main cleaning function"""
        if self.language == 'bangla':
            return self.clean_bangla_text(text)
        else:
            return self.clean_english_text(text)

    def clean_bangla_text(self, text):
        """Clean Bangla text"""
        # Unicode normalization
        text = unicodedata.normalize('NFC', text)

        # Remove zero-width characters
        text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)

        # Normalize whitespace
        text = self.normalize_whitespace(text)

        return text

    def clean_english_text(self, text):
        """Clean English text"""
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)

        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)

        # Normalize whitespace
        text = self.normalize_whitespace(text)

        return text

    def normalize_whitespace(self, text):
        """Remove extra whitespace"""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    def remove_html_tags(self, text):
        """Remove any remaining HTML tags"""
        return re.sub(r'<[^>]+>', '', text)
```

### Step 7: Implement Language Detection

Create `src/preprocessing/language_detector.py`:

```python
from langdetect import detect, detect_langs
import re

class LanguageDetector:
    """Detect document language"""

    def __init__(self, confidence_threshold=0.8):
        self.confidence_threshold = confidence_threshold

    def detect(self, text):
        """Detect language of text"""
        try:
            # Try langdetect first
            lang = detect(text)
            return self.map_language_code(lang)
        except:
            # Fallback to character-based detection
            return self.detect_by_characters(text)

    def get_confidence(self, text):
        """Get confidence score for language detection"""
        try:
            langs = detect_langs(text)
            if langs:
                return langs[0].prob
            return 0.0
        except:
            return 0.0

    def detect_by_characters(self, text):
        """Detect language by character range"""
        # Count Bangla characters (Unicode range: 0980-09FF)
        bangla_chars = len(re.findall(r'[\u0980-\u09FF]', text))

        # Count English characters
        english_chars = len(re.findall(r'[a-zA-Z]', text))

        total = bangla_chars + english_chars
        if total == 0:
            return 'unknown'

        bangla_ratio = bangla_chars / total

        if bangla_ratio > 0.5:
            return 'bangla'
        elif bangla_ratio < 0.2:
            return 'english'
        else:
            return 'mixed'

    def map_language_code(self, code):
        """Map langdetect codes to our language names"""
        mapping = {
            'bn': 'bangla',
            'en': 'english'
        }
        return mapping.get(code, code)

    def verify_language(self, text, expected_language):
        """Verify if text matches expected language"""
        detected = self.detect(text)
        confidence = self.get_confidence(text)

        if detected == expected_language and confidence >= self.confidence_threshold:
            return True
        return False
```

### Step 8: Run Full Pipeline

Now you can run the full data collection:

```bash
# Collect Bangla documents
python scripts/run_crawler.py --language bangla --target 2500

# Collect English documents
python scripts/run_crawler.py --language english --target 2500

# Or both at once
python scripts/run_crawler.py --language both --target 2500
```

### Step 9: Verify Results

Create a simple verification script `scripts/verify_data.py`:

```python
import json
from pathlib import Path
from collections import Counter

def verify_documents(file_path):
    """Verify collected documents"""
    documents = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            doc = json.loads(line)
            documents.append(doc)

    print(f"\n{'='*60}")
    print(f"Verification Report: {file_path.name}")
    print(f"{'='*60}\n")

    print(f"Total documents: {len(documents)}")

    # Count by source
    sources = Counter(doc['source'] for doc in documents)
    print(f"\nDocuments by source:")
    for source, count in sources.most_common():
        print(f"  {source}: {count}")

    # Check required fields
    required_fields = ['title', 'body', 'url', 'date', 'language']
    missing_fields = []
    for doc in documents:
        for field in required_fields:
            if field not in doc or not doc[field]:
                missing_fields.append((doc.get('doc_id', 'unknown'), field))

    if missing_fields:
        print(f"\n⚠ Warning: {len(missing_fields)} missing fields found")
    else:
        print(f"\n✓ All required fields present")

    # Check document length
    avg_length = sum(len(doc['body']) for doc in documents) / len(documents)
    print(f"\nAverage document length: {avg_length:.0f} characters")

    # Check date range
    dates = [doc.get('date', '') for doc in documents if doc.get('date')]
    if dates:
        print(f"Date range: {min(dates)} to {max(dates)}")

    print(f"\n{'='*60}\n")

if __name__ == '__main__':
    for lang in ['bangla', 'english']:
        file_path = Path(f"data/processed/{lang}_docs.json")
        if file_path.exists():
            verify_documents(file_path)
```

Run verification:
```bash
python scripts/verify_data.py
```

## Next Steps

After successfully collecting data:

1. Implement indexing (see `docs/module_a_implementation_plan.md`)
2. Build inverted index
3. Generate embeddings (optional)
4. Move to Module B (Query Processing)

## Common Issues & Solutions

### Issue 1: Crawling is too slow
**Solution**: Reduce delay between requests (but be respectful!)
```yaml
# config/crawler_config.yaml
crawler:
  delay_between_requests: 1  # Reduce to 1 second
```

### Issue 2: Getting blocked by websites
**Solution**: Use RSS feeds as fallback
```python
# Implement RSS crawler and use it when HTML scraping fails
```

### Issue 3: Encoding errors with Bangla text
**Solution**: Always use UTF-8 encoding
```python
with open(file_path, 'w', encoding='utf-8') as f:
    # ...
```

### Issue 4: Not enough documents
**Solution**:
- Crawl more pages (homepage + category pages)
- Use RSS feeds
- Check robots.txt for allowed paths

## Resources

- BeautifulSoup docs: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- Requests docs: https://requests.readthedocs.io/
- spaCy docs: https://spacy.io/
- langdetect: https://pypi.org/project/langdetect/

## Questions?

Refer to:
- Full implementation plan: `docs/module_a_implementation_plan.md`
- Project README: `README.md`
- Config files: `config/`
