"""Text cleaning and normalization"""

import re
import unicodedata


class TextCleaner:
    """Clean and normalize text for different languages"""

    def __init__(self, language):
        """
        Initialize text cleaner

        Args:
            language: 'bangla' or 'english'
        """
        self.language = language

    def clean(self, text):
        """
        Main cleaning method

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove HTML tags
        text = self.remove_html_tags(text)

        # Language-specific cleaning
        if self.language == 'bangla':
            text = self.clean_bangla(text)
        else:
            text = self.clean_english(text)

        # Common cleaning
        text = self.normalize_whitespace(text)

        return text

    def clean_bangla(self, text):
        """
        Clean Bangla text

        Args:
            text: Bangla text

        Returns:
            Cleaned text
        """
        # Unicode normalization (NFC form)
        text = unicodedata.normalize('NFC', text)

        # Remove zero-width characters
        text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)

        # Remove non-Bangla characters (keep basic punctuation)
        # Bangla range: 0980-09FF
        text = re.sub(r'[^\u0980-\u09FF\s.,!?;:()\-"\']', ' ', text)

        return text

    def clean_english(self, text):
        """
        Clean English text

        Args:
            text: English text

        Returns:
            Cleaned text
        """
        # Remove URLs
        text = re.sub(r'http\S+|www\.\S+', '', text)

        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)

        # Remove extra punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-"\']', ' ', text)

        return text

    def remove_html_tags(self, text):
        """
        Remove HTML tags

        Args:
            text: Text with possible HTML

        Returns:
            Text without HTML
        """
        return re.sub(r'<[^>]+>', '', text)

    def normalize_whitespace(self, text):
        """
        Normalize whitespace

        Args:
            text: Text with irregular whitespace

        Returns:
            Normalized text
        """
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    def get_cleaned_length(self, text):
        """
        Get length of cleaned text

        Args:
            text: Input text

        Returns:
            Character count
        """
        cleaned = self.clean(text)
        return len(cleaned)
