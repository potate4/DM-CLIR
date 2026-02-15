"""
Module D - Error Analysis
Analyze 5 required error categories using actual Module B components
Uses the same 22 queries as ranking and labeling for consistency
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.retrieval import BM25Retriever, FuzzyRetriever, SemanticRetriever
from src.evaluation import ErrorAnalyzer
from src.query_processing import QueryProcessor, QueryLanguageDetector, EntityMapper, QueryTranslator


# Same 22 queries used across all Module D scripts
TEST_QUERIES = [
    "Bangladesh national cricket team performance",
    "বাংলাদেশের অর্থনৈতিক প্রবৃদ্ধি পরিস্থিতি",
    "climate change এর প্রভাব in Bangladesh",
    "বাংলাদেশ নির্বাচন ও রাজনৈতিক অবস্থা",
    "Dhaka যানজট ও transport system",
    "garment শিল্পের শ্রমিকদের অবস্থা",
    "বাংলাদেশ technology startup ও digital innovation",
    "COVID-19 স্বাস্থ্য ও মহামারি পরিস্থিতি",
    "Bangladesh-India কূটনৈতিক relations",
    "গাজা যুদ্ধ ও ceasefire আপডেট",
    "women অধিকার ও gender equality",
    "শেয়ার বাজার ও অর্থনীতি পরিস্থিতি",
    "flood দুর্যোগ ও relief কার্যক্রম",
    "বাংলাদেশ জাতীয় football team খবর",
    "Rohingya শরণার্থী সংকট পরিস্থিতি",
    "bank loan সুদের হার বাংলাদেশ",
    "বিদ্যুৎ, power ও energy supply অবস্থা",
    "university শিক্ষার্থীদের protest আন্দোলন",
    "Trump এর America trade policy",
    "চালের দাম ও food inflation",
    "Greenland নিয়ে Trump এর territory মন্তব্য",
    "কৃত্রিম বুদ্ধিমত্তা ও Artificial Intelligence অগ্রগতি",
]


def load_documents():
    """Load documents from data/processed/"""
    documents = []

    for file_path in ['data/processed/english_docs.json', 'data/processed/bangla_docs.json']:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        doc = json.loads(line.strip())
                        documents.append(doc)
                    except:
                        continue

    # Ensure all docs have tokens
    for doc in documents:
        if 'tokens' not in doc or not doc['tokens']:
            text = (doc.get('title', '') + ' ' + doc.get('body', '')).lower()
            doc['tokens'] = [w for w in text.split() if len(w) > 1]

    return documents


def has_bangla(text):
    """Check if text contains Bangla characters"""
    return any('\u0980' <= c <= '\u09FF' for c in text)


def has_english(text):
    """Check if text contains English letters"""
    return any('a' <= c.lower() <= 'z' for c in text)


def is_code_switching(text):
    """Check if text mixes Bangla and English"""
    return has_bangla(text) and has_english(text)


def main():
    """Main execution"""
    print("=" * 80)
    print("MODULE D - ERROR ANALYSIS")
    print("Analyze 5 required error categories")
    print(f"Using {len(TEST_QUERIES)} queries (same as ranking/labeling)")
    print("=" * 80)

    # Load documents
    print("\n[1/6] Loading documents...")
    documents = load_documents()
    if not documents:
        print("No documents found!")
        return

    print(f"  Loaded {len(documents)} documents")

    # Initialize retrieval models
    print("\n[2/6] Initializing retrieval models...")
    bm25 = BM25Retriever(documents)
    fuzzy = FuzzyRetriever(documents)
    semantic = SemanticRetriever(documents, cache_file='data/embeddings_cache.pkl')
    print("  Models ready!")

    # Initialize Module B components
    print("\n[3/6] Initializing Module B components...")
    query_processor = QueryProcessor(expand_queries=True)
    language_detector = QueryLanguageDetector()
    entity_mapper = EntityMapper()
    translator = QueryTranslator()
    print("  Module B components ready!")

    # Initialize error analyzer
    analyzer = ErrorAnalyzer()

    print("\n" + "=" * 80)
    print("RUNNING ERROR ANALYSIS ON 22 QUERIES")
    print("=" * 80)

    # =========================================================================
    # Category 1: Translation Failures - Using actual Module B translator
    # Test on queries that have Bangla content needing translation
    # =========================================================================
    print("\n[4/6] Category 1: Translation Failures")
    print("-" * 60)

    # Select queries with significant Bangla content for translation analysis
    translation_queries = [q for q in TEST_QUERIES if has_bangla(q)][:10]

    for query in translation_queries:
        # Use actual Module B translation
        detected_lang = language_detector.detect(query)
        if detected_lang == 'bangla' or is_code_switching(query):
            translated = translator.translate(query, 'bangla', 'english')
            method_used = translator.get_method_used()

            # Run retrieval with both original and translated
            bm25_results = bm25.search(translated.lower().split(), top_k=10)
            semantic_results = semantic.search(query, top_k=10)

            analyzer.analyze_translation_failures(
                query=query,
                translation_data={
                    'original': query,
                    'translated': translated,
                    'method': method_used,
                    'expected': 'N/A'
                },
                retrieval_results={
                    'BM25': bm25_results,
                    'Semantic': semantic_results
                }
            )
            print(f"  {query[:50]}...")
            print(f"    -> '{translated[:50]}...' ({method_used})")

    # =========================================================================
    # Category 2: Named Entity Mismatch - Using actual Module B EntityMapper
    # =========================================================================
    print("\n[5/6] Category 2: Named Entity Mismatch")
    print("-" * 60)

    for query in TEST_QUERIES:
        # Use Module B to extract and map entities
        detected_lang = language_detector.detect(query)
        target_lang = 'english' if detected_lang == 'bangla' else 'bangla'
        entities = entity_mapper.extract_and_map(query, detected_lang, target_lang)

        if entities:  # Only analyze if entities found
            # Convert to format expected by error analyzer
            entity_info = []
            for ent in entities:
                entity_info.append({
                    'text': ent['original'],
                    'type': ent.get('label', 'ENTITY'),
                    'variants': [ent['original'], ent['mapped']] if ent['mapped'] != ent['original'] else [ent['original']],
                    'extraction_method': ent.get('extraction_method', 'unknown')
                })

            # Run retrieval
            query_tokens = query.lower().split()
            bm25_results = bm25.search(query_tokens, top_k=10)
            fuzzy_results = fuzzy.search(query, top_k=10)
            semantic_results = semantic.search(query, top_k=10)

            analyzer.analyze_entity_mismatch(
                query=query,
                entities=entity_info,
                retrieval_results={
                    'BM25': bm25_results,
                    'Fuzzy': fuzzy_results,
                    'Semantic': semantic_results
                }
            )
            print(f"  {query[:50]}...")
            print(f"    Entities: {[e['original'] for e in entities]}")

    # =========================================================================
    # Category 3: Semantic vs Lexical Wins - ALL queries
    # =========================================================================
    print("\n[6/6] Category 3-5: Semantic/Lexical, Cross-Script, Code-Switching")
    print("-" * 60)

    for query in TEST_QUERIES:
        # Run retrieval for all models
        query_tokens = query.lower().split()
        bm25_results = bm25.search(query_tokens, top_k=10)
        fuzzy_results = fuzzy.search(query, top_k=10)
        semantic_results = semantic.search(query, top_k=10)

        # Category 3: Semantic vs Lexical
        analyzer.analyze_semantic_lexical_wins(
            query=query,
            all_results={
                'BM25': bm25_results,
                'Semantic': semantic_results
            }
        )

        # Category 5: Code-Switching (for mixed queries)
        if is_code_switching(query):
            detected_lang = language_detector.detect(query)
            processed = query_processor.process(query)

            analyzer.analyze_code_switching(
                query=query,
                language_mix={
                    'detected_languages': ['english', 'bangla'],
                    'primary_language': detected_lang,
                    'code_switching_detected': True,
                    'translation_method': processed.get('translation_method', 'none'),
                    'variants_generated': len(processed.get('variants', []))
                },
                retrieval_results={
                    'BM25': bm25_results,
                    'Semantic': semantic_results
                }
            )

    # Category 4: Cross-Script Ambiguity - Test key entity variants
    cross_script_pairs = [
        ['Bangladesh', 'বাংলাদেশ'],
        ['Dhaka', 'ঢাকা'],
        ['cricket', 'ক্রিকেট'],
        ['India', 'ভারত'],
        ['Trump', 'ট্রাম্প'],
        ['football', 'ফুটবল'],
        ['Rohingya', 'রোহিঙ্গা'],
    ]

    for variants in cross_script_pairs:
        variant_results = {}
        for variant in variants:
            query_tokens = variant.lower().split()
            variant_results[variant] = {
                'BM25': bm25.search(query_tokens, top_k=10),
                'Fuzzy': fuzzy.search(variant, top_k=10),
                'Semantic': semantic.search(variant, top_k=10)
            }

        analyzer.analyze_cross_script_ambiguity(
            query_variants=variants,
            retrieval_results_per_variant=variant_results
        )

    print(f"  Analyzed all {len(TEST_QUERIES)} queries")

    # Generate and print report
    print("\n" + "=" * 80)
    analyzer.print_report()

    # Save report
    output_dir = 'data/evaluation/results/module_d_results'
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, 'error_analysis.json')
    analyzer.save_report(output_file)

    print(f"\nError analysis saved to: {output_file}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
