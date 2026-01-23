"""
System Evaluator
Evaluates retrieval system using labeled queries and calculates metrics
"""

import csv
import os
from collections import defaultdict
import pandas as pd
from .metrics import EvaluationMetrics


class SystemEvaluator:
    """
    Evaluate retrieval system using relevance labels
    """

    # Target thresholds from requirements
    TARGETS = {
        'precision@10': 0.6,
        'recall@50': 0.5,
        'ndcg@10': 0.5,
        'mrr': 0.4
    }

    def __init__(self, labels_file='data/evaluation/labeled_queries.csv'):
        """
        Initialize evaluator

        Args:
            labels_file (str): Path to CSV file with relevance labels
                Format: query, doc_id, doc_url, language, relevant, annotator
        """
        self.labels_file = labels_file
        self.labels = {}  # query -> set of relevant doc_ids
        self.all_labels = []  # List of all label dicts

        if os.path.exists(labels_file):
            self._load_labels()
        else:
            print(f"�  Labels file not found: {labels_file}")
            print("  Please run labeling tool first: python scripts/run_module_d_labeling.py")

    def _load_labels(self):
        """
        Load relevance labels from CSV

        CSV Format:
            query, doc_id, doc_url, language, relevant, annotator
        """
        self.labels = defaultdict(set)

        try:
            with open(self.labels_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    query = row['query'].strip()
                    doc_id = row.get('doc_id', '').strip()
                    doc_url = row['doc_url'].strip()
                    relevant = row['relevant'].strip().lower()

                    # Store full row
                    self.all_labels.append(row)

                    # If marked as relevant, add to query's relevant set
                    if relevant == 'yes':
                        # Use doc_id if available, otherwise use URL as identifier
                        identifier = doc_id if doc_id else doc_url
                        self.labels[query].add(identifier)

            print(f" Loaded {len(self.all_labels)} labels for {len(self.labels)} queries")

        except Exception as e:
            print(f"L Error loading labels: {e}")

    def get_queries(self):
        """
        Get list of labeled queries

        Returns:
            list: List of query strings
        """
        return list(self.labels.keys())

    def evaluate_model(self, model_name, retrieval_results):
        """
        Evaluate a single model

        Args:
            model_name (str): Name of the model ('BM25', 'Semantic', etc.)
            retrieval_results (dict): Mapping of query -> list of doc_ids
                {
                    'query1': ['doc1', 'doc2', 'doc3', ...],
                    'query2': ['doc5', 'doc6', ...],
                    ...
                }

        Returns:
            dict: Evaluation results
                {
                    'model': str,
                    'metrics': {
                        'precision@10': 0.62,
                        'recall@50': 0.54,
                        'ndcg@10': 0.58,
                        'mrr': 0.75
                    },
                    'per_query': [
                        {
                            'query': 'bangladesh cricket',
                            'precision@10': 0.7,
                            'recall@50': 0.6,
                            'ndcg@10': 0.65,
                            'mrr': 0.5,
                            'num_relevant': 3,
                            'num_retrieved_relevant': 2
                        },
                        ...
                    ],
                    'meets_targets': {
                        'precision@10': True,
                        'recall@50': True,
                        'ndcg@10': True,
                        'mrr': True
                    }
                }
        """
        per_query_metrics = []
        aggregated_metrics = {
            'precision@10': [],
            'recall@50': [],
            'ndcg@10': [],
            'mrr': []
        }

        for query in self.labels.keys():
            if query not in retrieval_results:
                print(f"�  Query not in results: {query}")
                continue

            retrieved = retrieval_results[query]
            relevant = self.labels[query]

            # Calculate metrics for this query
            metrics = EvaluationMetrics.calculate_all_metrics(
                retrieved, relevant,
                k_precision=10,
                k_recall=50,
                k_ndcg=10
            )

            # Count relevant docs retrieved
            relevant_retrieved = sum(1 for doc in retrieved[:50] if doc in relevant)

            query_result = {
                'query': query,
                **metrics,
                'num_relevant': len(relevant),
                'num_retrieved_relevant': relevant_retrieved
            }

            per_query_metrics.append(query_result)

            # Aggregate
            for metric_name, value in metrics.items():
                aggregated_metrics[metric_name].append(value)

        # Calculate averages
        avg_metrics = {}
        for metric_name, values in aggregated_metrics.items():
            avg_metrics[metric_name] = sum(values) / len(values) if values else 0.0

        # Check if targets are met
        meets_targets = {}
        for metric_name, target in self.TARGETS.items():
            meets_targets[metric_name] = avg_metrics.get(metric_name, 0) >= target

        return {
            'model': model_name,
            'metrics': avg_metrics,
            'per_query': per_query_metrics,
            'meets_targets': meets_targets,
            'num_queries': len(per_query_metrics)
        }

    def evaluate_all_models(self, all_results):
        """
        Evaluate all models and compare

        Args:
            all_results (dict): Results from all models
                {
                    'BM25': {
                        'query1': ['doc1', 'doc2', ...],
                        'query2': ['doc5', 'doc6', ...],
                    },
                    'Semantic': {...},
                    ...
                }

        Returns:
            dict: Comparison results
                {
                    'models': ['BM25', 'TF-IDF', 'Fuzzy', 'Semantic'],
                    'evaluations': {
                        'BM25': {...},
                        'Semantic': {...},
                        ...
                    },
                    'comparison_table': DataFrame,
                    'best_model': {
                        'precision@10': 'Semantic',
                        'recall@50': 'Semantic',
                        'ndcg@10': 'BM25',
                        'mrr': 'Semantic'
                    }
                }
        """
        evaluations = {}
        best_model = {}
        best_scores = {}

        # Evaluate each model
        for model_name, results in all_results.items():
            evaluation = self.evaluate_model(model_name, results)
            evaluations[model_name] = evaluation

            # Track best model for each metric
            for metric_name, score in evaluation['metrics'].items():
                if metric_name not in best_scores or score > best_scores[metric_name]:
                    best_scores[metric_name] = score
                    best_model[metric_name] = model_name

        # Create comparison table
        comparison_data = {}
        for model_name, evaluation in evaluations.items():
            comparison_data[model_name] = evaluation['metrics']

        comparison_table = pd.DataFrame(comparison_data).T

        return {
            'models': list(all_results.keys()),
            'evaluations': evaluations,
            'comparison_table': comparison_table,
            'best_model': best_model
        }

    def print_evaluation(self, evaluation):
        """
        Print formatted evaluation results

        Args:
            evaluation (dict): Output from evaluate_model()
        """
        print(f"\n{'='*70}")
        print(f"Evaluation Results: {evaluation['model']}")
        print(f"{'='*70}")
        print(f"Queries Evaluated: {evaluation['num_queries']}")
        print(f"\nMetrics:")
        print(f"{'-'*70}")

        for metric_name, value in evaluation['metrics'].items():
            target = self.TARGETS.get(metric_name, 0)
            status = " " if evaluation['meets_targets'].get(metric_name, False) else "L"
            print(f"  {metric_name:15s}: {value:.3f} (target e {target:.1f}) {status}")

        print(f"{'='*70}\n")

    def save_results(self, all_results, output_file):
        """
        Save evaluation results to JSON

        Args:
            all_results (dict): Output from evaluate_all_models()
            output_file (str): Path to output JSON file
        """
        import json

        # Convert DataFrame to dict for JSON serialization
        results_to_save = {
            'models': all_results['models'],
            'best_model': all_results['best_model'],
            'evaluations': {}
        }

        for model_name, evaluation in all_results['evaluations'].items():
            results_to_save['evaluations'][model_name] = {
                'metrics': evaluation['metrics'],
                'meets_targets': evaluation['meets_targets'],
                'num_queries': evaluation['num_queries']
            }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_to_save, f, indent=2)

        print(f" Results saved to {output_file}")


if __name__ == "__main__":
    # Test the evaluator
    print("Testing SystemEvaluator...")

    # Create dummy labels file
    labels_data = [
        {'query': 'cricket', 'doc_id': 'doc1', 'doc_url': 'http://url1', 'language': 'english', 'relevant': 'yes', 'annotator': 'test'},
        {'query': 'cricket', 'doc_id': 'doc3', 'doc_url': 'http://url3', 'language': 'english', 'relevant': 'yes', 'annotator': 'test'},
        {'query': 'cricket', 'doc_id': 'doc2', 'doc_url': 'http://url2', 'language': 'english', 'relevant': 'no', 'annotator': 'test'},
        {'query': 'education', 'doc_id': 'doc5', 'doc_url': 'http://url5', 'language': 'english', 'relevant': 'yes', 'annotator': 'test'},
    ]

    test_labels_file = 'test_labels.csv'
    with open(test_labels_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['query', 'doc_id', 'doc_url', 'language', 'relevant', 'annotator'])
        writer.writeheader()
        writer.writerows(labels_data)

    # Initialize evaluator
    evaluator = SystemEvaluator(labels_file=test_labels_file)

    # Dummy retrieval results
    bm25_results = {
        'cricket': ['doc1', 'doc2', 'doc3', 'doc4', 'doc5'],
        'education': ['doc5', 'doc6', 'doc7']
    }

    semantic_results = {
        'cricket': ['doc1', 'doc3', 'doc2', 'doc4', 'doc5'],
        'education': ['doc5', 'doc6', 'doc7']
    }

    # Evaluate BM25
    print("\n[Test] Evaluating BM25:")
    bm25_eval = evaluator.evaluate_model('BM25', bm25_results)
    evaluator.print_evaluation(bm25_eval)

    # Evaluate Semantic
    print("\n[Test] Evaluating Semantic:")
    semantic_eval = evaluator.evaluate_model('Semantic', semantic_results)
    evaluator.print_evaluation(semantic_eval)

    # Compare all models
    print("\n[Test] Comparing all models:")
    all_results_dict = {
        'BM25': bm25_results,
        'Semantic': semantic_results
    }
    comparison = evaluator.evaluate_all_models(all_results_dict)
    print("\nComparison Table:")
    print(comparison['comparison_table'])
    print(f"\nBest Models by Metric:")
    for metric, model in comparison['best_model'].items():
        print(f"  {metric:15s}: {model}")

    # Cleanup
    os.remove(test_labels_file)

    print("\n SystemEvaluator test passed!")
