"""Build inverted index from collected documents"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.indexing.document_store import DocumentStore
from src.indexing.inverted_index import InvertedIndex
from src.utils.logger import setup_logger


def build_index_for_language(language):
    """
    Build index for a language

    Args:
        language: 'bangla' or 'english'
    """
    logger = setup_logger(f'BuildIndex-{language}')

    logger.info(f"\n{'='*60}")
    logger.info(f"Building index for {language.upper()}")
    logger.info(f"{'='*60}\n")

    # Paths
    base_dir = Path(__file__).parent.parent
    docs_file = base_dir / 'data' / 'processed' / f'{language}_docs.json'
    index_file = base_dir / 'data' / 'indices' / f'{language}_index.pkl'

    # Load documents
    logger.info("Loading documents...")
    doc_store = DocumentStore()
    doc_store.load(docs_file)

    documents = doc_store.get_all_documents()
    logger.info(f"Loaded {len(documents)} documents")

    # Build index
    logger.info("Building inverted index...")
    index = InvertedIndex(language)
    index.build_from_documents(documents)

    # Save index
    logger.info("Saving index...")
    index.save(index_file)

    # Print statistics
    stats = index.get_statistics()
    logger.info(f"\n{'='*60}")
    logger.info(f"INDEX STATISTICS")
    logger.info(f"{'='*60}")
    logger.info(f"Total documents: {stats['total_documents']}")
    logger.info(f"Vocabulary size: {stats['vocabulary_size']}")
    logger.info(f"Avg doc length: {stats['average_document_length']} tokens")

    logger.info(f"\nTop 10 terms by document frequency:")
    for term, doc_freq in stats['top_terms']:
        logger.info(f"  {term}: {doc_freq} documents")

    logger.info(f"{'='*60}\n")


def main():
    """Main function"""
    print("\nBuilding Inverted Indices\n")

    # Build for both languages
    for language in ['bangla', 'english']:
        try:
            build_index_for_language(language)
        except Exception as e:
            print(f"Error building index for {language}: {str(e)}")
            continue

    print("✓ Index building complete!\n")


if __name__ == '__main__':
    main()
