"""
Module D - Evaluation
Calculate Precision@10, Recall@50, nDCG@10, MRR using labeled queries
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.retrieval import BM25Retriever, TFIDFRetriever, FuzzyRetriever, SemanticRetriever
from src.evaluation import SystemEvaluator


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
    print("MODULE D - EVALUATION")
    print("Calculate IR metrics using labeled queries")
    print("=" * 80)

    # Check if labels exist
    labels_file = 'data/evaluation/labeled_queries.csv'
    if not os.path.exists(labels_file):
        print("\nL Labels file not found!")
        print(f"Expected: {labels_file}")
        print("\nPlease run labeling first:")
        print("  python scripts/run_module_d_labeling.py")
        return

    # Initialize evaluator
    print(f"\n=� Loading relevance labels from {labels_file}...")
    evaluator = SystemEvaluator(labels_file=labels_file)

    queries = evaluator.get_queries()

    if not queries:
        print("L No queries found in labels file!")
        return

    print(f" Found labels for {len(queries)} queries")

    # Load documents
    print("\n=� Loading documents...")
    documents = load_documents()

    if not documents:
        print("L No documents found!")
        return

    print(f" Loaded {len(documents)} documents")

    # Initialize retrieval models
    print("\n=' Initializing retrieval models...")
    print("[1/4] BM25...")
    bm25 = BM25Retriever(documents)

    print("[2/4] TF-IDF...")
    tfidf = TFIDFRetriever(documents)

    print("[3/4] Fuzzy...")
    fuzzy = FuzzyRetriever(documents)

    print("[4/4] Semantic (LaBSE)...")
    semantic = SemanticRetriever(documents, cache_file='data/embeddings_cache.pkl')

    print(" All models ready!")

    # Run retrieval for all labeled queries
    print(f"\n=Running retrieval for {len(queries)} queries...")
    all_results = {}

    for model_name, retriever in [
        ('BM25', bm25),
        ('TF-IDF', tfidf),
        ('Fuzzy', fuzzy),
        ('Semantic', semantic)
    ]:
        print(f"  {model_name}...", end='', flush=True)
        model_results = {}

        for query in queries:
            query_tokens = query.lower().split()

            # Run retrieval
            if model_name in ['BM25', 'TF-IDF']:
                results = retriever.search(query_tokens, top_k=50)
            else:
                results = retriever.search(query, top_k=50)

            # Extract doc_ids
            doc_ids = []
            for result in results:
                doc = result.get('doc', {})
                # Use doc_id if available, otherwise URL
                doc_id = doc.get('doc_id', doc.get('url', ''))
                doc_ids.append(doc_id)

            model_results[query] = doc_ids

        all_results[model_name] = model_results
 
    print("  Retrieval complete!")

    # Evaluate all models
    print("\n=� Calculating metrics...")
    print("=" * 80)

    evaluations = {}
    for model_name in ['BM25', 'TF-IDF', 'Fuzzy', 'Semantic']:
        print(f"\nEvaluating {model_name}...")
        evaluation = evaluator.evaluate_model(model_name, all_results[model_name])
        evaluator.print_evaluation(evaluation)
        evaluations[model_name] = evaluation

    # Compare all models
    print("\n" + "=" * 80)
    print("MODEL COMPARISON")
    print("=" * 80)

    comparison = evaluator.evaluate_all_models(all_results)
    print("\nComparison Table:")
    print(comparison['comparison_table'])

    print("\nBest Model by Metric:")
    for metric, model in comparison['best_model'].items():
        print(f"  {metric:15s}: {model}")

    # Save results
    output_dir = 'data/evaluation/results/module_d_results'
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, 'evaluation_metrics.json')
    evaluator.save_results(comparison, output_file)

    # Save comparison table as CSV
    csv_file = os.path.join(output_dir, 'metrics_comparison.csv')
    comparison['comparison_table'].to_csv(csv_file)
    print(f"  Comparison table saved to {csv_file}")

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Queries evaluated: {len(queries)}")
    print(f"Models evaluated: {len(evaluations)}")
    print(f"\nTarget Thresholds:")
    for metric, target in evaluator.TARGETS.items():
        print(f"  {metric:15s}: e {target:.1f}")

    # Count how many models meet all targets
    models_meeting_all = sum(
        1 for eval in evaluations.values()
        if all(eval['meets_targets'].values())
    )

    print(f"\nModels meeting all targets: {models_meeting_all}/{len(evaluations)}")

    print(" " + "=" * 80)
    print("  Evaluation complete!")
    print(f"\nResults saved to:")
    print(f"  - {output_file}")
    print(f"  - {csv_file}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
