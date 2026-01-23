"""
Module D - Search Engine Comparison
Manual comparison with Google and Bing search results
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.retrieval import SemanticRetriever
from src.evaluation import SearchEngineComparison


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
    print("MODULE D - SEARCH ENGINE COMPARISON")
    print("Compare with Google and Bing")
    print("=" * 80)

    # Initialize comparison tool
    comparison = SearchEngineComparison(
        output_file='data/evaluation/search_engine_results.csv'
    )

    # Get queries to compare
    print("\nHow many queries would you like to compare?")
    print("(Recommendation: 3-5 queries)")
    try:
        num_queries = int(input("Number of queries: ").strip())
    except:
        num_queries = 3

    queries = []
    print(f"\nEnter {num_queries} queries:")
    for i in range(num_queries):
        query = input(f"  Query {i+1}: ").strip()
        if query:
            queries.append(query)

    if not queries:
        print("L No queries entered!")
        return

    print(f"\n  Will compare {len(queries)} queries")

    # Load documents
    print("\n=� Loading documents...")
    documents = load_documents()
    if not documents:
        print("L No documents found!")
        return

    print(f"  Loaded {len(documents)} documents")

    # Initialize semantic retriever (best for cross-lingual)
    print("\n=' Building Semantic retriever...")
    semantic = SemanticRetriever(documents, cache_file='data/embeddings_cache.pkl')
    print("  Model ready!")

    # Process each query
    all_comparisons = []

    for query in queries:
        print(f"\n{'=' * 80}")
        print(f"Query: \"{query}\"")
        print(f"{'=' * 80}")

        # Get our system's results
        print("\n=Running retrieval with our system...")
        our_results = semantic.search(query, top_k=10)
        print(f"  Retrieved {len(our_results)} results")

        # Collect manual Google/Bing results
        print("\n=� Now, please search for this query on Google and Bing")
        print("Then paste the results below.\n")

        manual_results = comparison.collect_manual_results(query, engines=['Google', 'Bing'])

        # Compare
        comp_result = comparison.compare_results(query, our_results)
        all_comparisons.append(comp_result)

        # Print comparison
        comparison.print_comparison(comp_result)

    # Save all comparisons
    output_dir = 'data/evaluation/results/module_d_results'
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, 'search_comparison.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_comparisons, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Queries compared: {len(all_comparisons)}")

    avg_google_overlap = sum(c['overlap_with_google'] for c in all_comparisons) / len(all_comparisons)
    avg_bing_overlap = sum(c['overlap_with_bing'] for c in all_comparisons) / len(all_comparisons)
    total_unique = sum(c['unique_results'] for c in all_comparisons)

    print(f"\nAverage overlap:")
    print(f"  With Google: {avg_google_overlap:.1%}")
    print(f"  With Bing: {avg_bing_overlap:.1%}")
    print(f"  Total unique results: {total_unique}")

    print(f"\nResults saved to:")
    print(f"  - {output_file}")
    print(f"  - data/evaluation/search_engine_results.csv")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
