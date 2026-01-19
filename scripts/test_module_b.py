"""Test Module B: Query Processing with proper NLP methods"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.query_processing.language_detector import QueryLanguageDetector
from src.query_processing.normalizer import QueryNormalizer
from src.query_processing.translator import QueryTranslator
from src.query_processing.expander import QueryExpander
from src.query_processing.entity_mapper import EntityMapper
from src.query_processing.query_processor import QueryProcessor


def test_language_detector():
    """Test language detection"""
    print("\n[1] Testing Language Detector...")

    detector = QueryLanguageDetector()

    tests = [
        ("education system", "english"),
        ("cricket match today", "english"),
        ("dhaka university", "english"),
    ]

    for query, expected in tests:
        result = detector.detect(query)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"  {status} '{query}' -> {result}")

    # Test Bangla
    bangla_query = "শিক্ষা ব্যবস্থা"
    result = detector.detect(bangla_query)
    print(f"  [OK] Bangla query -> {result}")

    print("  [PASS] Language detector working")


def test_normalizer():
    """Test query normalization"""
    print("\n[2] Testing Normalizer...")

    normalizer = QueryNormalizer()

    query = "  education   system   "
    result = normalizer.normalize(query, 'english')
    print(f"  Whitespace: '{query}' -> '{result}'")

    query = "EDUCATION System"
    result = normalizer.normalize(query, 'english')
    print(f"  Lowercase: '{query}' -> '{result}'")

    tokens = normalizer.tokenize("education system in bangladesh")
    print(f"  Tokens: {tokens}")

    print("  [PASS] Normalizer working")


def test_translator():
    """Test query translation with method reporting"""
    print("\n[3] Testing Translator...")

    translator = QueryTranslator()

    # Show available methods
    methods = translator.get_available_methods()
    available = [k for k, v in methods.items() if v]
    print(f"  Available methods: {', '.join(available)}")

    # Test translations
    tests = [
        ("education", "bangla"),
        ("politics", "bangla"),
        ("health system", "bangla"),
    ]

    for word, target in tests:
        result = translator.translate(word, 'english', target)
        method = translator.get_method_used()
        print(f"  '{word}' -> [{len(result)} chars] (method: {method})")

    print("  [PASS] Translator working")


def test_expander():
    """Test query expansion with method reporting"""
    print("\n[4] Testing Query Expander...")

    expander = QueryExpander(use_embeddings=False)  # Disable embeddings for faster test

    # Show available methods
    methods = expander.get_available_methods()
    available = [k for k, v in methods.items() if v]
    print(f"  Available methods: {', '.join(available)}")

    # Test expansion
    query = "education"
    result = expander.expand(query, 'english')
    expansions = result['expansions']
    methods_used = result['methods']

    print(f"  '{query}':")
    for word, terms in expansions.items():
        method = methods_used.get(word, 'none')
        print(f"    -> {terms[:4]}... (method: {method})")

    # Test multi-word
    query = "education sports"
    result = expander.expand(query, 'english')
    for word, terms in result['expansions'].items():
        method = result['methods'].get(word, 'none')
        print(f"  '{word}' -> {len(terms)} terms (method: {method})")

    print("  [PASS] Expander working")


def test_entity_mapper():
    """Test entity mapping with method reporting"""
    print("\n[5] Testing Entity Mapper...")

    mapper = EntityMapper()

    # Show available methods
    methods = mapper.get_available_methods()
    available = [k for k, v in methods.items() if v]
    print(f"  Available methods: {', '.join(available)}")

    # Test mappings
    tests = [
        ("bangladesh", "english", "bangla"),
        ("dhaka", "english", "bangla"),
    ]

    for entity, source, target in tests:
        result = mapper.map_entity(entity, source, target)
        print(f"  '{entity}' -> [{len(result)} chars]")

    # Test entity extraction
    text = "dhaka university cricket match"
    entities = mapper.extract_and_map(text, 'english', 'bangla')
    method = mapper.get_method_used()
    print(f"  Extracted {len(entities)} entities from '{text}' (method: {method})")

    for ent in entities[:2]:
        print(f"    - {ent['original']} -> [{len(ent['mapped'])} chars] ({ent['extraction_method']})")

    print("  [PASS] Entity mapper working")


def test_full_pipeline():
    """Test complete query processor with method summary"""
    print("\n[6] Testing Full Pipeline...")

    processor = QueryProcessor()

    # Show all available methods
    all_methods = processor.get_available_methods()
    print("\n  Available methods:")
    for component, methods in all_methods.items():
        available = [k for k, v in methods.items() if v]
        print(f"    {component}: {', '.join(available)}")

    # Test query
    query = "education in bangladesh"
    print(f"\n  Query: '{query}'")

    result = processor.process(query)

    print(f"  Language: {result['language']}")
    print(f"  Normalized: {result['normalized']}")
    print(f"  Translated: [{len(result['translated'])} chars]")
    print(f"  Entities: {len(result['entities'])}")
    print(f"  Variants: {len(result['variants'])} queries generated")

    # Show methods used
    print("\n  Methods used:")
    summary = result['methods_summary']
    print(f"    Translation: {summary['translation']}")
    print(f"    Entity extraction: {summary['entity_extraction']}")
    if summary['expansion']:
        print(f"    Expansion: {', '.join(summary['expansion'])}")

    print("\n  [PASS] Full pipeline working")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Testing Module B: Query Processing (with NLP methods)")
    print("="*60)

    try:
        test_language_detector()
        test_normalizer()
        test_translator()
        test_expander()
        test_entity_mapper()
        test_full_pipeline()

        print("\n" + "="*60)
        print("SUCCESS: All Module B tests passed!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\nERROR: Test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
