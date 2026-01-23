"""
Module D - Ranking Demo
Demonstrates ranking with all retrieval models, normalized scores, confidence warnings, and execution timing
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.retrieval import BM25Retriever, TFIDFRetriever, FuzzyRetriever, SemanticRetriever
from src.ranking import DocumentRanker, ConfidenceScorer, QueryProfiler


def load_documents():
    """
    Load documents from data/processed/

    Returns:
        list: Combined list of documents from both Bangla and English sources
    """
    documents = []

    # Load English documents
    english_path = 'data/processed/english_docs.json'
    if os.path.exists(english_path):
        print(f"=� Loading English documents from {english_path}...")
        with open(english_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    doc = json.loads(line.strip())
                    documents.append(doc)
                except:
                    continue
        print(f"   Loaded {len(documents)} English documents")

    # Load Bangla documents
    bangla_path = 'data/processed/bangla_docs.json'
    start_count = len(documents)
    if os.path.exists(bangla_path):
        print(f"=� Loading Bangla documents from {bangla_path}...")
        with open(bangla_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    doc = json.loads(line.strip())
                    documents.append(doc)
                except:
                    continue
        print(f"   Loaded {len(documents) - start_count} Bangla documents")

    # Ensure all docs have tokens
    print("\n=' Preparing documents...")
    for doc in documents:
        if 'tokens' not in doc or not doc['tokens']:
            text = (doc.get('title', '') + ' ' + doc.get('body', '')).lower()
            doc['tokens'] = [w for w in text.split() if len(w) > 1]

    print(f"\n=� Total documents loaded: {len(documents)}")
    return documents


def main():
    """Main execution"""
    print("=" * 80)
    print("MODULE D - RANKING DEMO")
    print("Demonstrating: Score Normalization, Confidence Warnings, Execution Timing")
    print("=" * 80)

    # Load documents
    documents = load_documents()

    if not documents:
        print("\nL No documents found!")
        print("Please ensure documents exist in:")
        print("  - data/processed/english_docs.json")
        print("  - data/processed/bangla_docs.json")
        return

    # Initialize retrieval models
    print("\n=' Initializing retrieval models...")
    print("[1/4] Building BM25...")
    bm25 = BM25Retriever(documents)

    print("[2/4] Building TF-IDF...")
    tfidf = TFIDFRetriever(documents)

    print("[3/4] Building Fuzzy...")
    fuzzy = FuzzyRetriever(documents)

    print("[4/4] Building Semantic (LaBSE)...")
    print("  (This may take 1-5 minutes for first-time embedding generation)")
    semantic = SemanticRetriever(documents, cache_file='data/embeddings_cache.pkl')

    print("\n All models ready!")

    # Initialize ranking components
    ranker = DocumentRanker()
    scorer = ConfidenceScorer(threshold=0.20)
    profiler = QueryProfiler()

    # Test queries (mix of English, Bangla, cross-lingual)
    test_queries = [
        "bangladesh cricket team",
        "economy growth",
        "���ͷ� �ͯ��ͥ�",  # education system in Bangla
    ]

    # Results storage
    all_results = []

    # Process each query
    for query in test_queries:
        with profiler.track_query(query):
            print(f"\n{'=' * 80}")
            print(f"Query: '{query}'")
            print(f"{'=' * 80}\n")

            query_results = {}

            # BM25 Retrieval
            with profiler.track_stage('bm25_retrieval'):
                query_tokens = query.lower().split()
                bm25_results = bm25.search(query_tokens, top_k=10)

            # Rank and normalize BM25 results
            bm25_ranked = ranker.rank_documents(bm25_results, 'BM25', top_k=10)
            bm25_confidence = scorer.evaluate_confidence(bm25_ranked)

            # Display BM25 results
            print(f"BM25 Results (Normalized):")
            print(f"{'-' * 70}")
            if bm25_ranked['results']:
                for r in bm25_ranked['results'][:5]:
                    title = r['doc'].get('title', 'No title')[:55]
                    print(f"  {r['rank']}. [{r['score']:.3f}] {title}")
            else:
                print("  (no results)")

            # Show confidence warning if needed
            if bm25_confidence['is_low_confidence']:
                print(f"\n   {bm25_confidence['warning_message']}")

            query_results['BM25'] = bm25_ranked

            # Semantic Retrieval
            print(f"\nSemantic Results (Normalized):")
            print(f"{'-' * 70}")

            with profiler.track_stage('semantic_retrieval'):
                semantic_results = semantic.search(query, top_k=10)

            # Rank and normalize Semantic results
            semantic_ranked = ranker.rank_documents(semantic_results, 'Semantic', top_k=10)
            semantic_confidence = scorer.evaluate_confidence(semantic_ranked)

            if semantic_ranked['results']:
                for r in semantic_ranked['results'][:5]:
                    title = r['doc'].get('title', 'No title')[:55]
                    print(f"  {r['rank']}. [{r['score']:.3f}] {title}")
            else:
                print("  (no results)")

            # Show confidence warning if needed
            if semantic_confidence['is_low_confidence']:
                print(f"\n   {semantic_confidence['warning_message']}")

            query_results['Semantic'] = semantic_ranked

            # Timing report
            timing = profiler.get_report(query)
            print(f"\n   Execution Time: {timing['total_time_ms']:.2f} ms")
            print(f"   Breakdown:")
            for stage, time_ms in timing['stages'].items():
                percentage = timing['breakdown_percentage'].get(stage, 0)
                print(f"     {stage:20s}: {time_ms:7.2f} ms ({percentage:5.1f}%)")

            # Store results
            all_results.append({
                'query': query,
                'results': query_results,
                'timing': timing,
                'confidence': {
                    'BM25': bm25_confidence,
                    'Semantic': semantic_confidence
                }
            })

    # Save results
    output_dir = 'data/evaluation/results/module_d_results'
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, 'ranking_results.json')

    # Prepare results for JSON (remove non-serializable objects)
    results_to_save = []
    for result in all_results:
        result_copy = {
            'query': result['query'],
            'timing': result['timing'],
            'confidence': {
                model: {
                    'is_low_confidence': conf['is_low_confidence'],
                    'top_score': conf['top_score'],
                    'threshold': conf['threshold']
                }
                for model, conf in result['confidence'].items()
            },
            'top_results': {
                model: [
                    {
                        'rank': r['rank'],
                        'score': r['score'],
                        'title': r['doc'].get('title', '')[:100]
                    }
                    for r in results['results'][:3]
                ]
                for model, results in result['results'].items()
            }
        }
        results_to_save.append(result_copy)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_to_save, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Queries tested: {len(test_queries)}")
    print(f"Models evaluated: BM25, Semantic")
    print(f"\nAll scores normalized to [0, 1] scale")
    print(f"Low-confidence threshold: {scorer.threshold}")
    print(f"\nResults saved to: {output_file}")
    print(f"{'=' * 80}\n")

    print(" Module D Ranking Demo Complete!")
    print("\nNext steps:")
    print("  1. Label queries: python scripts/run_module_d_labeling.py")
    print("  2. Run evaluation: python scripts/run_module_d_evaluation.py")
    print("  3. Error analysis: python scripts/run_module_d_error_analysis.py")


if __name__ == "__main__":
    main()
