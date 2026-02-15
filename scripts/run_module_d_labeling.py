"""
Module D - Relevance Labeling
Interactive tool for creating relevance labels for evaluation
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.retrieval import BM25Retriever, SemanticRetriever
from src.evaluation import RelevanceLabelingTool


def load_documents():
    """Load documents from data/processed/"""
    documents = []

    for file_path in ['data/processed/english_docs.json', 'data/processed/bangla_docs.json']:
        if os.path.exists(file_path):
            print(f"=� Loading from {file_path}...")
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

    print(f" Loaded {len(documents)} documents\n")
    return documents


def main():
    """Main execution"""
    print("=" * 80)
    print("MODULE D - RELEVANCE LABELING")
    print("Create relevance labels for evaluation")
    print("=" * 80)

    # Get user info
    print("\nBefore we start, please enter your name:")
    annotator = input("Annotator name: ").strip()
    if not annotator:
        annotator = 'user'

    # Load documents
    print("\n=� Loading documents...")
    documents = load_documents()

    if not documents:
        print("\nL No documents found!")
        return

    # Initialize retrieval models
    print("=' Initializing retrieval models...")
    print("  Building BM25...")
    bm25 = BM25Retriever(documents)

    print("  Building Semantic (this may take a few minutes)...")
    semantic = SemanticRetriever(documents, cache_file='data/embeddings_cache.pkl')

    print(" Models ready!\n")

    # Get queries to label
    # Option 1: Use predefined queries
    # Option 2: Let user input queries

    print("How would you like to select queries to label?")
    print("  1. Use default test queries")
    print("  2. Enter custom queries")
    choice = input("Enter choice (1 or 2): ").strip()

    queries = []
    if choice == '2':
        print("\nEnter queries to label (one per line, empty line to finish):")
        while True:
            query = input("  Query: ").strip()
            if not query:
                break
            queries.append(query)
    else:
        # Default queries
        queries = [
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
        print(f"\nUsing {len(queries)} default test queries")

    if not queries:
        print("L No queries to label!")
        return

    # Run retrieval for all queries
    print(f"\n= Running retrieval for {len(queries)} queries...")
    retrieval_results = {}

    for query in queries:
        print(f"  Processing: {query}")
        query_tokens = query.lower().split()

        # Use both BM25 and Semantic for better coverage
        bm25_results = bm25.search(query_tokens, top_k=10)
        semantic_results = semantic.search(query, top_k=10)

        retrieval_results[query] = {
            'BM25': bm25_results,
            'Semantic': semantic_results
        }

    print(" Retrieval complete!\n")

    # Start labeling
    tool = RelevanceLabelingTool(
        queries=queries,
        retrieval_results=retrieval_results,
        output_file='data/evaluation/labeled_queries.csv'
    )

    print("=" * 80)
    print("INSTRUCTIONS")
    print("=" * 80)
    print("For each query, you will see the top-10 retrieved documents.")
    print("For each document, mark it as:")
    print("  - 'y' or 'yes' if it's relevant to the query")
    print("  - 'n' or 'no' if it's not relevant")
    print("  - 'skip' to skip uncertain cases")
    print("  - 'quit' to stop labeling")
    print("")
    print("Your labels will be saved incrementally after each query.")
    print("=" * 80)

    input("\nPress Enter to start labeling...")

    # Start interactive labeling
    labels_created = tool.start_labeling_session(
        annotator_name=annotator,
        max_docs_per_query=10
    )

    # Show statistics
    print("\n" + "=" * 80)
    print("LABELING COMPLETE")
    print("=" * 80)
    tool.print_statistics()

    print("Next steps:")
    print("  1. Run evaluation: python scripts/run_module_d_evaluation.py")
    print("  2. Error analysis: python scripts/run_module_d_error_analysis.py")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
