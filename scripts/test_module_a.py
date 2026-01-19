"""Simple test for Module A components"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.preprocessing.text_cleaner import TextCleaner
from src.preprocessing.language_detector import LanguageDetector
from src.preprocessing.tokenizer import Tokenizer
from src.indexing.document_store import DocumentStore
from src.indexing.inverted_index import InvertedIndex


def test_text_cleaner():
    """Test text cleaner"""
    print("\n[1] Testing Text Cleaner...")

    # Bangla
    cleaner_bn = TextCleaner('bangla')
    text_bn = "  এটি একটি   পরীক্ষা  <b>text</b>  "
    cleaned_bn = cleaner_bn.clean(text_bn)
    print(f"  Bangla: cleaned {len(cleaned_bn)} chars (original: {len(text_bn)})")

    # English
    cleaner_en = TextCleaner('english')
    text_en = "  This is a   TEST  <b>text</b>  http://example.com  "
    cleaned_en = cleaner_en.clean(text_en)
    print(f"  English: '{text_en}' -> '{cleaned_en}'")

    print("  [OK] Text cleaner working")


def test_language_detector():
    """Test language detector"""
    print("\n[2] Testing Language Detector...")

    detector = LanguageDetector()

    # Bangla text
    text_bn = "এটি বাংলা ভাষায় লেখা একটি বাক্য"
    lang_bn = detector.detect(text_bn)
    conf_bn = detector.get_confidence(text_bn)
    print(f"  Bangla text -> {lang_bn} (confidence: {conf_bn:.2f})")

    # English text
    text_en = "This is a sentence written in English"
    lang_en = detector.detect(text_en)
    conf_en = detector.get_confidence(text_en)
    print(f"  '{text_en}' -> {lang_en} (confidence: {conf_en:.2f})")

    # Mixed text
    text_mixed = "This is বাংলা mixed text"
    lang_mixed = detector.detect(text_mixed)
    print(f"  Mixed text -> {lang_mixed}")

    print("  [OK] Language detector working")


def test_tokenizer():
    """Test tokenizer"""
    print("\n[3] Testing Tokenizer...")

    # Bangla
    tokenizer_bn = Tokenizer('bangla')
    text_bn = "এটি একটি পরীক্ষা"
    tokens_bn = tokenizer_bn.tokenize(text_bn)
    print(f"  Bangla: {len(tokens_bn)} tokens")

    # English
    tokenizer_en = Tokenizer('english')
    text_en = "This is a TEST"
    tokens_en = tokenizer_en.tokenize(text_en)
    print(f"  English tokens: {tokens_en}")

    print("  [OK] Tokenizer working")


def test_document_store():
    """Test document store"""
    print("\n[4] Testing Document Store...")

    doc_store = DocumentStore()

    # Add sample documents
    docs = [
        {
            'doc_id': 'test_001',
            'title': 'Test Article 1',
            'body': 'This is the first test article',
            'language': 'english',
            'source': 'Test Source',
            'word_count': 6
        },
        {
            'doc_id': 'test_002',
            'title': 'Test Article 2',
            'body': 'This is the second test article',
            'language': 'bangla',
            'source': 'Test Source',
            'word_count': 6
        }
    ]

    doc_store.add_documents(docs)
    print(f"  Added {doc_store.get_count()} documents")

    # Test retrieval
    doc = doc_store.get_document('test_001')
    print(f"  Retrieved: {doc['title']}")

    # Test statistics
    stats = doc_store.get_statistics()
    print(f"  Stats: {stats}")

    print("  [OK] Document store working")


def test_inverted_index():
    """Test inverted index"""
    print("\n[5] Testing Inverted Index...")

    # Create sample documents
    docs = [
        {
            'doc_id': 'doc1',
            'body': 'information retrieval is important'
        },
        {
            'doc_id': 'doc2',
            'body': 'retrieval systems use inverted index'
        },
        {
            'doc_id': 'doc3',
            'body': 'information systems are complex'
        }
    ]

    # Build index
    index = InvertedIndex('english')
    index.build_from_documents(docs)

    print(f"  Vocabulary size: {index.get_vocabulary_size()}")

    # Test search
    term = 'information'
    postings = index.get_postings(term)
    print(f"  Postings for '{term}': {postings}")

    doc_freq = index.get_document_frequency('retrieval')
    print(f"  Document frequency for 'retrieval': {doc_freq}")

    print("  [OK] Inverted index working")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Testing Module A Components")
    print("="*60)

    try:
        test_text_cleaner()
        test_language_detector()
        test_tokenizer()
        test_document_store()
        test_inverted_index()

        print("\n" + "="*60)
        print("SUCCESS: All tests passed!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\nERROR: Test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
