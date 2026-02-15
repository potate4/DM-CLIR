"""
Module D - Search Engine Comparison
Compare our system results with Google and Bing
Uses the same 22 queries as ranking/labeling for consistency
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.retrieval import SemanticRetriever
from src.evaluation import SearchEngineComparison


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

    # Show available queries
    print(f"\nAvailable queries ({len(TEST_QUERIES)} total):")
    print("-" * 60)
    for i, q in enumerate(TEST_QUERIES, 1):
        print(f"  {i:2}. {q[:55]}{'...' if len(q) > 55 else ''}")

    # Select queries to compare
    print("\n" + "-" * 60)
    print("How many queries to compare? (Recommended: 3-5 for manual comparison)")
    print("Enter a number, or specific indices like '1,3,5,10'")

    choice = input("Selection [default=5]: ").strip()

    if not choice:
        queries = TEST_QUERIES[:5]
    elif ',' in choice:
        # Specific indices
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            queries = [TEST_QUERIES[i] for i in indices if 0 <= i < len(TEST_QUERIES)]
        except:
            queries = TEST_QUERIES[:5]
    else:
        try:
            num = int(choice)
            queries = TEST_QUERIES[:num]
        except:
            queries = TEST_QUERIES[:5]

    if not queries:
        print("No queries selected!")
        return

    print(f"\nSelected {len(queries)} queries for comparison")

    # Load documents
    print("\nLoading documents...")
    documents = load_documents()
    if not documents:
        print("No documents found!")
        return

    print(f"  Loaded {len(documents)} documents")

    # Initialize semantic retriever (best for cross-lingual)
    print("\nBuilding Semantic retriever...")
    semantic = SemanticRetriever(documents, cache_file='data/embeddings_cache.pkl')
    print("  Model ready!")

    # Process each query
    all_comparisons = []

    for idx, query in enumerate(queries, 1):
        print(f"\n{'=' * 80}")
        print(f"[{idx}/{len(queries)}] Query: \"{query}\"")
        print(f"{'=' * 80}")

        # Get our system's results
        print("\nOur system's results:")
        our_results = semantic.search(query, top_k=10)
        for i, r in enumerate(our_results[:5], 1):
            title = r.get('doc', {}).get('title', 'No title')[:50]
            score = r.get('score', 0)
            print(f"  {i}. [{score:.3f}] {title}")

        # Collect manual Google/Bing results
        print("\n" + "-" * 60)
        print("Search this query on Google and Bing.")
        print("Paste top 5-10 URLs from each (one per line, empty to finish):")

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

    if all_comparisons:
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
