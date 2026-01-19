"""Verify collected data quality"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.indexing.document_store import DocumentStore
from src.preprocessing.language_detector import LanguageDetector


def verify_language_data(language):
    """
    Verify data for a language

    Args:
        language: 'bangla' or 'english'
    """
    print(f"\n{'='*60}")
    print(f"Verifying {language.upper()} data")
    print(f"{'='*60}\n")

    # Load documents
    base_dir = Path(__file__).parent.parent
    docs_file = base_dir / 'data' / 'processed' / f'{language}_docs.json'

    if not docs_file.exists():
        print(f"❌ File not found: {docs_file}")
        return

    doc_store = DocumentStore()
    doc_store.load(docs_file)

    documents = doc_store.get_all_documents()
    print(f"Total documents: {len(documents)}")

    # Check required fields
    required_fields = ['doc_id', 'title', 'body', 'url', 'date', 'language', 'source']
    missing_fields = []

    for doc in documents:
        for field in required_fields:
            if field not in doc or not doc[field]:
                missing_fields.append((doc.get('doc_id', 'unknown'), field))

    if missing_fields:
        print(f"\n⚠️  Warning: {len(missing_fields)} missing fields")
        # Show first 5
        for doc_id, field in missing_fields[:5]:
            print(f"  - {doc_id}: missing '{field}'")
    else:
        print("✓ All required fields present")

    # Language verification
    detector = LanguageDetector()
    lang_correct = 0
    lang_incorrect = 0

    for doc in documents:
        detected = detector.detect(doc['body'])
        if detected == language:
            lang_correct += 1
        else:
            lang_incorrect += 1

    accuracy = (lang_correct / len(documents) * 100) if documents else 0
    print(f"\nLanguage detection accuracy: {accuracy:.1f}%")
    print(f"  Correct: {lang_correct}")
    print(f"  Incorrect: {lang_incorrect}")

    # Statistics
    stats = doc_store.get_statistics()

    print(f"\n📊 Statistics:")
    print(f"  Average word count: {stats['average_word_count']}")

    print(f"\n  Documents by source:")
    for source, count in sorted(stats['by_source'].items()):
        print(f"    {source}: {count}")

    # Check document lengths
    short_docs = [doc for doc in documents if doc.get('word_count', 0) < 100]
    if short_docs:
        print(f"\n⚠️  Warning: {len(short_docs)} documents < 100 words")

    print(f"\n{'='*60}\n")


def main():
    """Main function"""
    print("\n🔍 Data Verification\n")

    for language in ['bangla', 'english']:
        verify_language_data(language)

    print("✓ Verification complete!\n")


if __name__ == '__main__':
    main()
