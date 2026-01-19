"""Language detection for documents"""

import re


class LanguageDetector:
    """Detect language of text (Bangla or English)"""

    def __init__(self, confidence_threshold=0.7):
        """
        Initialize language detector

        Args:
            confidence_threshold: Minimum confidence for detection
        """
        self.confidence_threshold = confidence_threshold

    def detect(self, text):
        """
        Detect language of text

        Args:
            text: Input text

        Returns:
            'bangla', 'english', or 'mixed'
        """
        if not text or len(text.strip()) == 0:
            return 'unknown'

        # Count character types
        bangla_chars = len(re.findall(r'[\u0980-\u09FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))

        total = bangla_chars + english_chars

        if total == 0:
            return 'unknown'

        # Calculate ratio
        bangla_ratio = bangla_chars / total

        # Determine language
        if bangla_ratio > 0.5:
            return 'bangla'
        elif bangla_ratio < 0.2:
            return 'english'
        else:
            return 'mixed'

    def get_confidence(self, text):
        """
        Get confidence score for detection

        Args:
            text: Input text

        Returns:
            Confidence score (0-1)
        """
        if not text:
            return 0.0

        bangla_chars = len(re.findall(r'[\u0980-\u09FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total = bangla_chars + english_chars

        if total == 0:
            return 0.0

        # Confidence is how dominant the detected language is
        bangla_ratio = bangla_chars / total
        english_ratio = english_chars / total

        return max(bangla_ratio, english_ratio)

    def verify_language(self, text, expected_language):
        """
        Verify if text matches expected language

        Args:
            text: Input text
            expected_language: Expected language ('bangla' or 'english')

        Returns:
            Boolean
        """
        detected = self.detect(text)
        confidence = self.get_confidence(text)

        return (detected == expected_language and
                confidence >= self.confidence_threshold)

    def is_bangla(self, text):
        """Check if text is Bangla"""
        return self.detect(text) == 'bangla'

    def is_english(self, text):
        """Check if text is English"""
        return self.detect(text) == 'english'

    def is_mixed(self, text):
        """Check if text is mixed language"""
        return self.detect(text) == 'mixed'
