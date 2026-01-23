"""
Module D - Error Analysis
Analyze 5 required error categories
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.retrieval import BM25Retriever, FuzzyRetriever, SemanticRetriever
from src.evaluation import ErrorAnalyzer


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


def main():
    """Main execution"""
    print("=" * 80)
    print("MODULE D - ERROR ANALYSIS")
    print("Analyze 5 required error categories")
    print("=" * 80)

    # Load documents
    print("\n=� Loading documents...")
    documents = load_documents()
    if not documents:
        print("L No documents found!")
        return

    print(f" Loaded {len(documents)} documents")

    # Initialize retrieval models
    print("\n=' Initializing retrieval models...")
    bm25 = BM25Retriever(documents)
    fuzzy = FuzzyRetriever(documents)
    semantic = SemanticRetriever(documents, cache_file='data/embeddings_cache.pkl')
    print(" Models ready!")

    # Initialize error analyzer
    analyzer = ErrorAnalyzer()

    # Test queries demonstrating each error category
    test_cases = {
        'cross_lingual': [
            ("���ͷ�", "Education in Bangla - semantic should win"),
            ("����", "Dhaka in Bangla - entity mismatch"),
            ("������Ƕ", "Bangladesh in Bangla"),
        ],
        'mixed_script': [
            ("Bangladesh cricket", "Mixed query"),
        ]
    }

    print("\n" + "=" * 80)
    print("RUNNING ERROR ANALYSIS")
    print("=" * 80)

    # Category 3: Semantic vs Lexical
    print("\n[1/5] Analyzing Semantic vs Lexical Performance...")
    for query, description in test_cases['cross_lingual']:
        print(f"  Query: {query} - {description}")

        # Run retrieval
        query_tokens = query.lower().split()
        bm25_results = bm25.search(query_tokens, top_k=10)
        semantic_results = semantic.search(query, top_k=10)

        # Analyze
        analyzer.analyze_semantic_lexical_wins(
            query=query,
            all_results={
                'BM25': bm25_results,
                'Semantic': semantic_results
            }
        )

    # Category 2: Named Entity Mismatch
    print("\n[2/5] Analyzing Named Entity Mismatch...")
    entity_query = "���� economy"
    print(f"  Query: {entity_query}")

    bm25_results = bm25.search(entity_query.lower().split(), top_k=10)
    fuzzy_results = fuzzy.search(entity_query, top_k=10)
    semantic_results = semantic.search(entity_query, top_k=10)

    analyzer.analyze_entity_mismatch(
        query=entity_query,
        entities=[{'text': '����', 'type': 'GPE', 'variants': ['Dhaka', 'Dacca']}],
        retrieval_results={
            'BM25': bm25_results,
            'Fuzzy': fuzzy_results,
            'Semantic': semantic_results
        }
    )

    # Category 4: Cross-Script Ambiguity
    print("\n[3/5] Analyzing Cross-Script Ambiguity...")
    variants = ['Bangladesh', '������Ƕ']
    print(f"  Variants: {variants}")

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

    # Category 5: Code-Switching
    print("\n[4/5] Analyzing Code-Switching...")
    mixed_query = "Bangladesh � cricket"
    print(f"  Query: {mixed_query}")

    bm25_results = bm25.search(mixed_query.lower().split(), top_k=10)
    semantic_results = semantic.search(mixed_query, top_k=10)

    analyzer.analyze_code_switching(
        query=mixed_query,
        language_mix={
            'detected_languages': ['english', 'bangla'],
            'code_switching_detected': True
        },
        retrieval_results={
            'BM25': bm25_results,
            'Semantic': semantic_results
        }
    )

    # Category 1: Translation Failures (simulated)
    print("\n[5/5] Analyzing Translation Failures (simulated)...")
    # Note: Actual translation failures would require running Module B
    # For demo, we'll add a simulated case
    analyzer.analyze_translation_failures(
        query="�ǯ���",
        translation_data={
            'original': '�ǯ���',
            'translated': 'chairman',  # Wrong: should be 'chair'
            'method': 'hypothetical',
            'expected': 'chair'
        },
        retrieval_results={
            'BM25': bm25.search(['chairman'], top_k=10),
            'Semantic': semantic.search('�ǯ���', top_k=10)
        }
    )

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
