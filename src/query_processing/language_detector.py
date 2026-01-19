"""Language detection for queries"""

import re


class QueryLanguageDetector:
    """Detect language of search queries"""

    # Bangla Unicode range: 0980-09FF
    BANGLA_PATTERN = re.compile(r'[\u0980-\u09FF]')
    ENGLISH_PATTERN = re.compile(r'[a-zA-Z]')

    def detect(self, query):
        """
        Detect query language

        Args:
            query: Search query string

        Returns:
            'bangla', 'english', or 'mixed'
        """
        if not query or not query.strip():
            return 'unknown'

        bangla_count = len(self.BANGLA_PATTERN.findall(query))
        english_count = len(self.ENGLISH_PATTERN.findall(query))
        total = bangla_count + english_count

        if total == 0:
            return 'unknown'

        bangla_ratio = bangla_count / total

        if bangla_ratio > 0.6:
            return 'bangla'
        elif bangla_ratio < 0.2:
            return 'english'
        else:
            return 'mixed'

    def get_confidence(self, query):
        """
        Get detection confidence score

        Args:
            query: Search query

        Returns:
            Confidence score (0-1)
        """
        if not query:
            return 0.0

        bangla_count = len(self.BANGLA_PATTERN.findall(query))
        english_count = len(self.ENGLISH_PATTERN.findall(query))
        total = bangla_count + english_count

        if total == 0:
            return 0.0

        # Return the dominance of the detected language
        return max(bangla_count, english_count) / total

    def is_bangla(self, query):
        """Check if query is Bangla"""
        return self.detect(query) == 'bangla'

    def is_english(self, query):
        """Check if query is English"""
        return self.detect(query) == 'english'

    def is_mixed(self, query):
        """Check if query contains both languages"""
        return self.detect(query) == 'mixed'
