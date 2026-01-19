"""Document storage and retrieval"""

import json
from pathlib import Path
from collections import Counter

from ..utils.logger import setup_logger


class DocumentStore:
    """Store and manage documents"""

    def __init__(self):
        """Initialize document store"""
        self.documents = {}  # doc_id -> document
        self.logger = setup_logger('DocumentStore')

    def add_document(self, document):
        """
        Add a document to the store

        Args:
            document: Document dict with doc_id
        """
        doc_id = document.get('doc_id')
        if not doc_id:
            self.logger.warning("Document missing doc_id, skipping")
            return

        self.documents[doc_id] = document

    def add_documents(self, documents):
        """
        Add multiple documents

        Args:
            documents: List of document dicts
        """
        for doc in documents:
            self.add_document(doc)

    def get_document(self, doc_id):
        """
        Get document by ID

        Args:
            doc_id: Document ID

        Returns:
            Document dict or None
        """
        return self.documents.get(doc_id)

    def get_documents_by_language(self, language):
        """
        Get all documents in a language

        Args:
            language: 'bangla' or 'english'

        Returns:
            List of documents
        """
        return [doc for doc in self.documents.values()
                if doc.get('language') == language]

    def get_all_documents(self):
        """Get all documents"""
        return list(self.documents.values())

    def get_count(self):
        """Get total document count"""
        return len(self.documents)

    def get_statistics(self):
        """
        Get dataset statistics

        Returns:
            Statistics dict
        """
        if not self.documents:
            return {}

        docs = list(self.documents.values())

        # Count by language
        languages = Counter(doc.get('language') for doc in docs)

        # Count by source
        sources = Counter(doc.get('source') for doc in docs)

        # Average word count
        word_counts = [doc.get('word_count', 0) for doc in docs]
        avg_words = sum(word_counts) / len(word_counts) if word_counts else 0

        stats = {
            'total_documents': len(docs),
            'by_language': dict(languages),
            'by_source': dict(sources),
            'average_word_count': round(avg_words, 2)
        }

        return stats

    def save(self, filepath):
        """
        Save documents to JSON file

        Args:
            filepath: Path to save file
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Save as newline-delimited JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            for doc in self.documents.values():
                f.write(json.dumps(doc, ensure_ascii=False) + '\n')

        self.logger.info(f"Saved {len(self.documents)} documents to {filepath}")

    def load(self, filepath):
        """
        Load documents from JSON file

        Args:
            filepath: Path to JSON file
        """
        filepath = Path(filepath)
        if not filepath.exists():
            self.logger.error(f"File not found: {filepath}")
            return

        count = 0
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    doc = json.loads(line)
                    self.add_document(doc)
                    count += 1

        self.logger.info(f"Loaded {count} documents from {filepath}")

    def save_metadata_csv(self, filepath):
        """
        Save metadata as CSV

        Args:
            filepath: Path to CSV file
        """
        import csv

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            if not self.documents:
                return

            # Get fields from first document
            sample_doc = list(self.documents.values())[0]
            fields = ['doc_id', 'title', 'url', 'date', 'language', 'source', 'word_count']

            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()

            for doc in self.documents.values():
                row = {field: doc.get(field, '') for field in fields}
                writer.writerow(row)

        self.logger.info(f"Saved metadata CSV to {filepath}")
