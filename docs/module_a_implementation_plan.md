# Module A Implementation Plan: Dataset Construction & Indexing

## Overview
Module A is responsible for collecting, preprocessing, and indexing multilingual documents (Bangla and English) from news websites.

**Target**: 2,500+ documents per language (5,000+ total)
**Marks**: 20% (12% construction + 8% indexing)
**Timeline**: Week 1

---

## Phase 1: Web Crawling (Days 1-3)

### 1.1 Base Crawler Infrastructure

**File**: `src/crawler/base_crawler.py`

**Key Components**:
```python
class BaseCrawler:
    - __init__(config, language)
    - fetch_page(url)              # GET request with retry logic
    - parse_html(html_content)     # BeautifulSoup parsing
    - extract_links(soup)          # Extract article URLs
    - save_raw_data(data)          # Save to JSON
    - respect_robots_txt(url)      # Check robots.txt
    - add_delay()                  # Delay between requests
```

**Features**:
- Configurable delay between requests (2 seconds default)
- Retry logic with exponential backoff (max 3 retries)
- User-Agent rotation to avoid blocking
- Error logging for failed requests
- Progress tracking (documents collected)
- Respectful crawling (robots.txt, rate limiting)

### 1.2 News-Specific Crawler

**File**: `src/crawler/news_crawler.py`

**Key Components**:
```python
class NewsCrawler(BaseCrawler):
    - crawl_site(site_config)
    - extract_article_links(page_html, selectors)
    - parse_article(article_url, selectors)
    - extract_metadata(soup, selectors)
    - validate_article(article_data)
```

**Article Extraction**:
- Title: Extract from `<h1>` or configured selector
- Body: Concatenate all `<p>` tags in article
- URL: Store original article URL
- Date: Parse from `<time>` or date meta tags
- Language: Auto-detect using langdetect

**Validation**:
- Minimum body length: 100 characters
- Maximum body length: 50,000 characters
- Valid title (not empty)
- Valid date format

### 1.3 RSS Feed Crawler (Fallback)

**File**: `src/crawler/rss_crawler.py`

**Purpose**: If HTML scraping fails, use RSS feeds

**Key Components**:
```python
class RSSCrawler(BaseCrawler):
    - parse_rss_feed(feed_url)
    - extract_entries(parsed_feed)
    - fetch_full_article(entry_link)
```

**RSS Parsing**:
- Use `feedparser` library
- Extract title, link, published date from RSS
- Fetch full article content from link
- Fallback if HTML scraping fails

### 1.4 Crawling Strategy

**Target Distribution**:
- 5 Bangla sites × 500 docs each = 2,500 Bangla docs
- 5 English sites × 500 docs each = 2,500 English docs

**Approach**:
1. Start with homepage or `/latest` section
2. Extract article links from homepage
3. For each article link, fetch and parse article
4. Save raw HTML and extracted data
5. Continue until target reached per site
6. If blocked or errors, try RSS feed
7. Log all errors and retries

**Error Handling**:
- 404 errors: Log and skip
- Timeout: Retry with longer timeout
- Encoding errors: Try multiple encodings (utf-8, utf-16, iso-8859-1)
- Connection errors: Exponential backoff

---

## Phase 2: Text Preprocessing (Days 3-4)

### 2.1 Text Cleaning

**File**: `src/preprocessing/text_cleaner.py`

**Key Components**:
```python
class TextCleaner:
    - remove_html_tags(text)           # Strip any remaining HTML
    - normalize_whitespace(text)       # Remove extra spaces/newlines
    - remove_special_chars(text)       # Remove non-alphanumeric (keep Bangla)
    - clean_bangla_text(text)          # Bangla-specific cleaning
    - clean_english_text(text)         # English-specific cleaning
```

**Bangla-Specific Cleaning**:
- Unicode normalization (NFC)
- Remove zero-width characters
- Fix common encoding issues
- Preserve Bangla punctuation
- Remove English characters if >90% Bangla

**English-Specific Cleaning**:
- Lowercase conversion
- Remove URLs, email addresses
- Expand contractions (don't → do not)
- Remove extra punctuation

### 2.2 Language Detection

**File**: `src/preprocessing/language_detector.py`

**Key Components**:
```python
class LanguageDetector:
    - detect(text)                      # Detect language
    - get_confidence()                  # Confidence score
    - verify_language(text, expected)   # Verify expected language
```

**Implementation**:
- Use `langdetect` library
- Confidence threshold: 0.8
- If confidence < 0.8, manual inspection
- Cross-check with expected language from site

**Language Codes**:
- Bangla: `bn`
- English: `en`

### 2.3 Metadata Extraction

**File**: `src/preprocessing/metadata_extractor.py`

**Key Components**:
```python
class MetadataExtractor:
    - extract_date(date_string)         # Parse various date formats
    - extract_source(url)               # Extract source name from URL
    - count_tokens(text)                # Token count
    - extract_named_entities(text)      # NER (optional)
```

**Metadata Fields (Required)**:
- `title`: String
- `body`: String
- `url`: String
- `date`: ISO format (YYYY-MM-DD)
- `language`: "bangla" or "english"
- `source`: Site name

**Metadata Fields (Optional)**:
- `token_count`: Integer
- `word_count`: Integer
- `named_entities`: List of entities
- `raw_html`: Original HTML (for debugging)

### 2.4 Tokenization

**File**: `src/preprocessing/tokenizer.py`

**Key Components**:
```python
class MultilingualTokenizer:
    - tokenize_bangla(text)
    - tokenize_english(text)
    - count_tokens(tokens)
```

**Bangla Tokenization**:
- Use spaCy or custom tokenizer
- Handle Bangla word boundaries
- Preserve compound words

**English Tokenization**:
- Use spaCy English tokenizer
- Remove stop words (optional)
- Lemmatization (optional)

---

## Phase 3: Data Storage (Days 4-5)

### 3.1 Document Storage Format

**File**: `data/processed/documents.json`

**Schema**:
```json
{
  "doc_id": "unique_id_12345",
  "title": "আর্টিকেল শিরোনাম",
  "body": "আর্টিকেল বডি টেক্সট...",
  "url": "https://example.com/article",
  "date": "2025-01-15",
  "language": "bangla",
  "source": "Prothom Alo",
  "token_count": 450,
  "word_count": 380,
  "named_entities": ["ঢাকা", "বাংলাদেশ"],
  "crawled_at": "2025-01-18T10:30:00Z"
}
```

**Storage Strategy**:
- Save as newline-delimited JSON (NDJSON)
- One document per line
- Easy to stream and process
- Can split into `bangla_docs.json` and `english_docs.json`

### 3.2 Metadata CSV

**File**: `data/processed/metadata.csv`

**Columns**:
```csv
doc_id,title,url,date,language,source,token_count,word_count
doc_001,Title here,https://...,2025-01-15,bangla,Prothom Alo,450,380
doc_002,Title here,https://...,2025-01-16,english,Daily Star,520,440
```

**Purpose**:
- Quick overview of dataset
- Easy filtering and analysis
- Compatible with pandas

### 3.3 File Organization

```
data/
├── raw/
│   ├── bangla/
│   │   ├── prothom_alo_001.json
│   │   ├── prothom_alo_002.json
│   │   └── ...
│   └── english/
│       ├── daily_star_001.json
│       └── ...
├── processed/
│   ├── documents.json          # All documents
│   ├── bangla_docs.json        # Bangla only
│   ├── english_docs.json       # English only
│   └── metadata.csv            # Metadata table
└── indices/
    └── (will be created in Phase 4)
```

---

## Phase 4: Indexing (Days 5-6)

### 4.1 Document Store

**File**: `src/indexing/document_store.py`

**Key Components**:
```python
class DocumentStore:
    - __init__(data_path)
    - load_documents()                  # Load from JSON
    - get_document(doc_id)              # Retrieve by ID
    - get_documents_by_language(lang)   # Filter by language
    - get_statistics()                  # Dataset stats
```

**Functionality**:
- In-memory document storage for fast access
- Dictionary mapping: `doc_id → document_data`
- Language-based filtering
- Statistics: doc count, avg length, etc.

### 4.2 Inverted Index

**File**: `src/indexing/inverted_index.py`

**Key Components**:
```python
class InvertedIndex:
    - __init__(documents, language)
    - build_index()                     # Build inverted index
    - tokenize_document(text)           # Tokenize
    - add_document(doc_id, tokens)      # Add to index
    - get_postings(term)                # Get doc IDs for term
    - get_term_frequency(term, doc_id)  # TF for term in doc
    - get_document_frequency(term)      # DF for term
    - save_index(path)                  # Serialize to disk
    - load_index(path)                  # Load from disk
```

**Index Structure**:
```python
{
  "term1": {
    "doc_001": {"tf": 5, "positions": [0, 45, 78, 120, 200]},
    "doc_005": {"tf": 2, "positions": [10, 95]}
  },
  "term2": { ... }
}
```

**Features**:
- Separate indices for Bangla and English
- Store term frequency (TF)
- Store term positions (for phrase queries)
- Calculate document frequency (DF)
- Support for incremental updates

### 4.3 Embeddings Store (Optional but Recommended)

**File**: `src/indexing/embeddings_store.py`

**Key Components**:
```python
class EmbeddingsStore:
    - __init__(model_name)
    - load_model()                      # Load embedding model
    - encode_documents(documents)       # Batch encoding
    - encode_query(query)               # Single encoding
    - save_embeddings(path)             # Save to disk
    - load_embeddings(path)             # Load from disk
```

**Recommended Models**:
1. **LaBSE** (Language-agnostic BERT Sentence Embeddings)
   - Model: `sentence-transformers/LaBSE`
   - Dimensions: 768
   - Best for cross-lingual retrieval

2. **XLM-RoBERTa** (Cross-lingual RoBERTa)
   - Model: `xlm-roberta-base`
   - Dimensions: 768
   - State-of-the-art multilingual

3. **mBERT** (Multilingual BERT)
   - Model: `bert-base-multilingual-cased`
   - Dimensions: 768
   - Stable and widely used

**Storage Format**:
```python
{
  "doc_001": [0.123, -0.456, 0.789, ...],  # 768-dim vector
  "doc_002": [0.234, -0.567, 0.890, ...],
  ...
}
```

**Implementation**:
- Use HuggingFace `sentence-transformers`
- Batch processing for efficiency
- GPU support if available
- Store as numpy array or pickle

### 4.4 Index Statistics

**Features to Track**:
- Total documents indexed
- Total unique terms
- Average document length
- Average terms per document
- Most frequent terms (per language)
- Vocabulary size (per language)

---

## Phase 5: Testing & Validation (Days 6-7)

### 5.1 Unit Tests

**File**: `tests/test_crawler.py`
- Test URL fetching
- Test HTML parsing
- Test error handling

**File**: `tests/test_preprocessing.py`
- Test text cleaning
- Test language detection
- Test tokenization

**File**: `tests/test_indexing.py`
- Test inverted index construction
- Test term lookup
- Test TF/DF calculation

### 5.2 Integration Tests

**Test Scenarios**:
1. End-to-end crawling (small sample)
2. Document processing pipeline
3. Index building and querying
4. Embedding generation

### 5.3 Data Validation

**Validation Checks**:
- [ ] At least 2,500 Bangla documents
- [ ] At least 2,500 English documents
- [ ] All documents have required metadata
- [ ] Language detection accuracy > 95%
- [ ] No duplicate documents (check URL)
- [ ] Date parsing success rate > 90%
- [ ] Average document length reasonable (>100 words)

### 5.4 Quality Checks

**Manual Inspection**:
- Sample 10 random Bangla documents
- Sample 10 random English documents
- Check for:
  - Proper text extraction
  - No HTML artifacts
  - Correct language labeling
  - Readable content
  - Proper date formatting

---

## Implementation Scripts

### Script 1: Run Crawler

**File**: `scripts/run_crawler.py`

```python
"""
Usage:
  python scripts/run_crawler.py --language bangla --target 2500
  python scripts/run_crawler.py --language english --target 2500
  python scripts/run_crawler.py --language both --target 2500
"""

import argparse
from src.crawler.news_crawler import NewsCrawler
from src.utils.logger import setup_logger

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--language', choices=['bangla', 'english', 'both'])
    parser.add_argument('--target', type=int, default=2500)
    args = parser.parse_args()

    # Load config and run crawler
    # ...
```

### Script 2: Build Index

**File**: `scripts/build_index.py`

```python
"""
Usage:
  python scripts/build_index.py
  python scripts/build_index.py --embeddings
"""

import argparse
from src.indexing.inverted_index import InvertedIndex
from src.indexing.embeddings_store import EmbeddingsStore

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--embeddings', action='store_true')
    args = parser.parse_args()

    # Build inverted index
    # Optionally build embeddings
    # ...
```

---

## Technical Challenges & Solutions

### Challenge 1: Website Structure Differences
**Problem**: Each news site has different HTML structure
**Solution**:
- Configurable CSS selectors in `config/sites.json`
- Multiple selector fallbacks
- RSS feed as backup

### Challenge 2: Bangla Text Encoding
**Problem**: Encoding issues with Bangla Unicode
**Solution**:
- Use UTF-8 everywhere
- Unicode normalization (NFC)
- Handle multiple encoding attempts

### Challenge 3: Rate Limiting / Blocking
**Problem**: Websites may block crawlers
**Solution**:
- Respect robots.txt
- Add delays (2 seconds minimum)
- Rotate User-Agent strings
- Use RSS feeds if blocked

### Challenge 4: Date Parsing
**Problem**: Inconsistent date formats
**Solution**:
- Use `dateparser` library
- Try multiple formats
- Manual patterns for common formats

### Challenge 5: Duplicate Content
**Problem**: Same article on multiple pages
**Solution**:
- Check URL uniqueness
- Hash content for exact duplicates
- Near-duplicate detection (Simhash)

---

## Deliverables

### Code Files
- [ ] `src/crawler/base_crawler.py`
- [ ] `src/crawler/news_crawler.py`
- [ ] `src/crawler/rss_crawler.py`
- [ ] `src/crawler/utils.py`
- [ ] `src/preprocessing/text_cleaner.py`
- [ ] `src/preprocessing/language_detector.py`
- [ ] `src/preprocessing/tokenizer.py`
- [ ] `src/preprocessing/metadata_extractor.py`
- [ ] `src/indexing/document_store.py`
- [ ] `src/indexing/inverted_index.py`
- [ ] `src/indexing/embeddings_store.py`

### Data Files
- [ ] `data/processed/documents.json` (5,000+ docs)
- [ ] `data/processed/bangla_docs.json` (2,500+ docs)
- [ ] `data/processed/english_docs.json` (2,500+ docs)
- [ ] `data/processed/metadata.csv`
- [ ] `data/indices/inverted_index.pkl`
- [ ] `data/indices/embeddings/` (if using embeddings)

### Scripts
- [ ] `scripts/run_crawler.py`
- [ ] `scripts/build_index.py`

### Tests
- [ ] `tests/test_crawler.py`
- [ ] `tests/test_preprocessing.py`
- [ ] `tests/test_indexing.py`

### Documentation
- [ ] Data collection report (stats, errors, challenges)
- [ ] Sample documents (5 Bangla + 5 English)
- [ ] Index statistics

---

## Success Criteria

1. ✅ **Quantity**: 2,500+ docs per language (5,000+ total)
2. ✅ **Quality**: All required metadata present
3. ✅ **Diversity**: Documents from all 10 sources
4. ✅ **Language**: >95% language detection accuracy
5. ✅ **Index**: Functional inverted index
6. ✅ **Embeddings**: Document embeddings generated (optional)
7. ✅ **Error Rate**: <5% failed documents
8. ✅ **Documentation**: Clear code with comments
9. ✅ **Tests**: All tests passing

---

## Next Steps

After Module A completion:
1. Integrate with Module B (Query Processing)
2. Provide document store interface for retrieval models
3. Share index structure with teammates
4. Document API for other modules to use

---

## Timeline Summary

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Crawler implementation | Working crawler |
| 2-3 | Data collection | Raw documents |
| 3-4 | Preprocessing | Cleaned documents |
| 4-5 | Data storage | JSON/CSV files |
| 5-6 | Indexing | Inverted index |
| 6-7 | Testing & validation | Quality report |

**Total**: 7 days (Week 1)
