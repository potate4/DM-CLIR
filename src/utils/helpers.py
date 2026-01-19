"""Helper utilities for CLIR project"""

import re
import hashlib
from datetime import datetime
from urllib.parse import urlparse


def generate_doc_id(url, title=""):
    """
    Generate unique document ID from URL

    Args:
        url: Document URL
        title: Document title (optional)

    Returns:
        Unique document ID
    """
    content = f"{url}{title}".encode('utf-8')
    hash_obj = hashlib.md5(content)
    return hash_obj.hexdigest()[:12]


def clean_url(url):
    """
    Clean and normalize URL

    Args:
        url: Raw URL

    Returns:
        Cleaned URL
    """
    url = url.strip()
    # Remove query parameters and fragments for deduplication
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def is_valid_url(url):
    """
    Check if URL is valid

    Args:
        url: URL to validate

    Returns:
        Boolean
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def parse_date(date_string):
    """
    Parse date string to ISO format

    Args:
        date_string: Date in various formats

    Returns:
        ISO format date string (YYYY-MM-DD)
    """
    if not date_string:
        return datetime.now().strftime('%Y-%m-%d')

    # Try common formats
    formats = [
        '%Y-%m-%d',
        '%d-%m-%Y',
        '%Y/%m/%d',
        '%d/%m/%Y',
        '%B %d, %Y',
        '%d %B %Y',
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_string.strip(), fmt)
            return dt.strftime('%Y-%m-%d')
        except:
            continue

    # If all fail, return current date
    return datetime.now().strftime('%Y-%m-%d')


def count_words(text):
    """
    Count words in text

    Args:
        text: Input text

    Returns:
        Word count
    """
    words = re.findall(r'\S+', text)
    return len(words)
