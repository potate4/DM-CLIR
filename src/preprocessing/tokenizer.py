"""Simple tokenizer for Bangla and English"""

import re


class Tokenizer:
    """Simple tokenizer for multilingual text"""

    def __init__(self, language):
        """
        Initialize tokenizer

        Args:
            language: 'bangla' or 'english'
        """
        self.language = language

    def tokenize(self, text):
        """
        Tokenize text into words

        Args:
            text: Input text

        Returns:
            List of tokens
        """
        if not text:
            return []

        if self.language == 'bangla':
            return self.tokenize_bangla(text)
        else:
            return self.tokenize_english(text)

    def tokenize_bangla(self, text):
        """
        Tokenize Bangla text

        Args:
            text: Bangla text

        Returns:
            List of tokens
        """
        # Split on whitespace and punctuation, keep Bangla characters
        tokens = re.findall(r'[\u0980-\u09FF]+', text)
        return [t for t in tokens if t]

    def tokenize_english(self, text):
        """
        Tokenize English text

        Args:
            text: English text

        Returns:
            List of tokens
        """
        # Lowercase
        text = text.lower()

        # Split on non-alphanumeric
        tokens = re.findall(r'\b[a-z]+\b', text)
        return [t for t in tokens if t]

    def count_tokens(self, text):
        """
        Count tokens in text

        Args:
            text: Input text

        Returns:
            Token count
        """
        tokens = self.tokenize(text)
        return len(tokens)
