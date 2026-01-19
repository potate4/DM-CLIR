"""Query normalization"""

import re
import unicodedata


class QueryNormalizer:
    """Normalize search queries"""

    # Common English stopwords (optional removal)
    ENGLISH_STOPWORDS = {
        'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'must', 'shall',
        'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
        'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
        'through', 'during', 'before', 'after', 'above', 'below',
        'between', 'under', 'again', 'further', 'then', 'once',
        'and', 'but', 'or', 'nor', 'so', 'yet', 'both', 'either',
        'neither', 'not', 'only', 'own', 'same', 'than', 'too',
        'very', 'just', 'also'
    }

    # Common Bangla stopwords
    BANGLA_STOPWORDS = {
        'এবং', 'ও', 'বা', 'কিন্তু', 'তবে', 'যে', 'এই', 'সেই',
        'এক', 'একটি', 'একটা', 'কোন', 'কোনো', 'যা', 'তা', 'এটা',
        'সেটা', 'এটি', 'সেটি', 'হয়', 'হবে', 'হয়েছে', 'হয়েছিল',
        'করা', 'করে', 'করেন', 'করেছে', 'থেকে', 'জন্য', 'দিয়ে',
        'নিয়ে', 'সাথে', 'মধ্যে', 'উপর', 'নিচে', 'পরে', 'আগে'
    }

    def __init__(self, remove_stopwords=False):
        """
        Initialize normalizer

        Args:
            remove_stopwords: Whether to remove stopwords
        """
        self.remove_stopwords = remove_stopwords

    def normalize(self, query, language=None):
        """
        Normalize a query

        Args:
            query: Raw query string
            language: 'bangla' or 'english' (auto-detect if None)

        Returns:
            Normalized query string
        """
        if not query:
            return ""

        # Basic cleaning
        query = self._clean_whitespace(query)

        # Language-specific normalization
        if language == 'bangla':
            query = self._normalize_bangla(query)
        elif language == 'english':
            query = self._normalize_english(query)
        else:
            # Apply both
            query = self._normalize_bangla(query)
            query = self._normalize_english(query)

        # Optional stopword removal
        if self.remove_stopwords:
            query = self._remove_stopwords(query, language)

        return query.strip()

    def _clean_whitespace(self, text):
        """Remove extra whitespace"""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _normalize_bangla(self, text):
        """Normalize Bangla text"""
        # Unicode normalization (NFC)
        text = unicodedata.normalize('NFC', text)

        # Remove zero-width characters
        text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)

        return text

    def _normalize_english(self, text):
        """Normalize English text"""
        # Lowercase
        text = text.lower()
        return text

    def _remove_stopwords(self, text, language=None):
        """Remove stopwords from text"""
        words = text.split()
        filtered = []

        for word in words:
            word_lower = word.lower()

            # Check against both stopword sets if language not specified
            if language == 'english':
                if word_lower not in self.ENGLISH_STOPWORDS:
                    filtered.append(word)
            elif language == 'bangla':
                if word not in self.BANGLA_STOPWORDS:
                    filtered.append(word)
            else:
                # Check both
                if (word_lower not in self.ENGLISH_STOPWORDS and
                    word not in self.BANGLA_STOPWORDS):
                    filtered.append(word)

        return ' '.join(filtered)

    def tokenize(self, query):
        """
        Simple tokenization

        Args:
            query: Normalized query

        Returns:
            List of tokens
        """
        # Split on whitespace and punctuation
        tokens = re.findall(r'[\w\u0980-\u09FF]+', query)
        return tokens
