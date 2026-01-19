"""Inverted index for document retrieval"""

import pickle
from pathlib import Path
from collections import defaultdict

from ..preprocessing.tokenizer import Tokenizer
from ..utils.logger import setup_logger


class InvertedIndex:
    """Simple inverted index"""

    def __init__(self, language):
        """
        Initialize inverted index

        Args:
            language: 'bangla' or 'english'
        """
        self.language = language
        self.index = defaultdict(dict)  # term -> {doc_id: term_freq}
        self.doc_lengths = {}  # doc_id -> document length
        self.tokenizer = Tokenizer(language)
        self.logger = setup_logger(f'Index-{language}')

    def add_document(self, doc_id, text):
        """
        Add document to index

        Args:
            doc_id: Document ID
            text: Document text
        """
        # Tokenize
        tokens = self.tokenizer.tokenize(text)

        # Count term frequencies
        term_freq = defaultdict(int)
        for token in tokens:
            term_freq[token] += 1

        # Add to index
        for term, freq in term_freq.items():
            self.index[term][doc_id] = freq

        # Store document length
        self.doc_lengths[doc_id] = len(tokens)

    def build_from_documents(self, documents):
        """
        Build index from list of documents

        Args:
            documents: List of document dicts
        """
        self.logger.info(f"Building index for {len(documents)} documents")

        for i, doc in enumerate(documents):
            doc_id = doc.get('doc_id')
            text = doc.get('body', '')

            if doc_id and text:
                self.add_document(doc_id, text)

            if (i + 1) % 500 == 0:
                self.logger.info(f"Indexed {i + 1} documents")

        self.logger.info(f"Index built: {len(self.index)} unique terms")

    def get_postings(self, term):
        """
        Get posting list for a term

        Args:
            term: Search term

        Returns:
            Dict of {doc_id: term_freq}
        """
        return self.index.get(term, {})

    def get_term_frequency(self, term, doc_id):
        """
        Get term frequency in a document

        Args:
            term: Search term
            doc_id: Document ID

        Returns:
            Term frequency (int)
        """
        return self.index.get(term, {}).get(doc_id, 0)

    def get_document_frequency(self, term):
        """
        Get document frequency for a term

        Args:
            term: Search term

        Returns:
            Number of documents containing term
        """
        return len(self.index.get(term, {}))

    def get_document_length(self, doc_id):
        """
        Get document length (token count)

        Args:
            doc_id: Document ID

        Returns:
            Document length
        """
        return self.doc_lengths.get(doc_id, 0)

    def get_vocabulary_size(self):
        """Get number of unique terms"""
        return len(self.index)

    def get_statistics(self):
        """
        Get index statistics

        Returns:
            Statistics dict
        """
        total_docs = len(self.doc_lengths)
        vocab_size = len(self.index)

        avg_doc_length = (sum(self.doc_lengths.values()) / total_docs
                          if total_docs > 0 else 0)

        # Most common terms
        term_doc_counts = [(term, len(postings))
                           for term, postings in self.index.items()]
        term_doc_counts.sort(key=lambda x: x[1], reverse=True)
        top_terms = term_doc_counts[:10]

        stats = {
            'total_documents': total_docs,
            'vocabulary_size': vocab_size,
            'average_document_length': round(avg_doc_length, 2),
            'top_terms': top_terms
        }

        return stats

    def save(self, filepath):
        """
        Save index to file

        Args:
            filepath: Path to save file
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'language': self.language,
            'index': dict(self.index),
            'doc_lengths': self.doc_lengths
        }

        with open(filepath, 'wb') as f:
            pickle.dump(data, f)

        self.logger.info(f"Saved index to {filepath}")

    def load(self, filepath):
        """
        Load index from file

        Args:
            filepath: Path to index file
        """
        filepath = Path(filepath)
        if not filepath.exists():
            self.logger.error(f"File not found: {filepath}")
            return

        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        self.language = data['language']
        self.index = defaultdict(dict, data['index'])
        self.doc_lengths = data['doc_lengths']

        self.logger.info(f"Loaded index from {filepath}")
