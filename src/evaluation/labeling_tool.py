"""
Relevance Labeling Tool
Interactive tool for creating relevance labels for evaluation
"""

import csv
import os
from datetime import datetime


class RelevanceLabelingTool:
    """
    Interactive tool for manual relevance labeling
    Helps user create relevance judgments for query results
    """

    def __init__(self, queries, retrieval_results, output_file='data/evaluation/labeled_queries.csv'):
        """
        Initialize labeling session

        Args:
            queries (list): List of query strings to label
            retrieval_results (dict): Results from retrieval models
                {
                    'query1': {
                        'BM25': [{'doc': {...}, 'score': 0.8, ...}, ...],
                        'Semantic': [...]
                    },
                    ...
                }
            output_file (str): Where to save labels
        """
        self.queries = queries
        self.results = retrieval_results
        self.output_file = output_file
        self.labels = []

        # Load existing labels if file exists
        if os.path.exists(output_file):
            self._load_existing_labels()

    def _load_existing_labels(self):
        """Load existing labels from CSV"""
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.labels = list(reader)
            print(f"9  Loaded {len(self.labels)} existing labels from {self.output_file}")
        except Exception as e:
            print(f"�  Could not load existing labels: {e}")

    def _is_query_labeled(self, query):
        """Check if query has already been labeled"""
        return any(label['query'] == query for label in self.labels)

    def start_labeling_session(self, annotator_name='user', max_docs_per_query=10):
        """
        Start interactive labeling session

        For each query:
          1. Show query
          2. Display top-K results from best model (usually Semantic)
          3. User marks each as relevant (y) or not (n)
          4. Save to CSV incrementally

        Args:
            annotator_name (str): Name of the person doing labeling
            max_docs_per_query (int): Maximum documents to label per query (default 10)

        Returns:
            int: Number of labels created
        """
        print("=" * 80)
        print("RELEVANCE LABELING TOOL")
        print("=" * 80)
        print(f"You will label up to {len(self.queries)} queries")
        print(f"For each query, mark documents as relevant (y) or not (n)")
        print("You can also skip uncertain cases by typing 'skip'")
        print("=" * 80)

        labels_created = 0

        for i, query in enumerate(self.queries, 1):
            # Skip if already labeled
            if self._is_query_labeled(query):
                print(f"\n[{i}/{len(self.queries)}] Query already labeled, skipping: {query}")
                continue

            print(f"\n{'=' * 80}")
            print(f"Query {i}/{len(self.queries)}")
            print(f"{'=' * 80}")

            labels_created += self._label_query(query, annotator_name, max_docs_per_query)

            # Save after each query (incremental save to prevent data loss)
            self._save_labels()

        print(f"\n{'=' * 80}")
        print(f" Labeling Complete!")
        print(f"Total labels created: {labels_created}")
        print(f"Saved to: {self.output_file}")
        print(f"{'=' * 80}\n")

        return labels_created

    def _label_query(self, query, annotator, max_docs):
        """
        Label one query interactively

        Args:
            query (str): Query text
            annotator (str): Annotator name
            max_docs (int): Maximum documents to show

        Returns:
            int: Number of labels created
        """
        print(f"\nQuery: \"{query}\"")
        print(f"{'-' * 80}\n")

        # Get results from Semantic model (usually best for cross-lingual)
        # Fall back to other models if Semantic not available
        if query not in self.results:
            print(f"�  No results found for query: {query}")
            return 0

        query_results = self.results[query]

        # Try to get results from best model
        model_priority = ['Semantic', 'BM25', 'TF-IDF', 'Fuzzy']
        results = None
        model_used = None

        for model in model_priority:
            if model in query_results and query_results[model]:
                results = query_results[model][:max_docs]
                model_used = model
                break

        if not results:
            print(f"�  No results available for this query")
            return 0

        print(f"Showing top-{len(results)} results from {model_used} model:\n")

        labels_created = 0

        for i, result in enumerate(results, 1):
            doc = result.get('doc', {})
            score = result.get('score', 0)

            # Display document info
            print(f"[{i}/{len(results)}] Score: {score:.3f}")
            print(f"  Title: {doc.get('title', 'No title')[:70]}")

            # Show snippet of body if available
            body = doc.get('body', '')
            if body:
                snippet = body[:150] + '...' if len(body) > 150 else body
                print(f"  Body: {snippet}")

            print(f"  URL: {doc.get('url', 'No URL')}")
            print(f"  Language: {doc.get('language', 'unknown')}")

            # Get user input
            while True:
                response = input("\n  Relevant? (y/n/skip/quit): ").lower().strip()

                if response in ['y', 'yes']:
                    relevant = 'yes'
                    break
                elif response in ['n', 'no']:
                    relevant = 'no'
                    break
                elif response == 'skip':
                    print("  Skipped\n")
                    continue
                elif response in ['quit', 'q']:
                    print("\n�  Labeling interrupted by user")
                    return labels_created
                else:
                    print("  Please enter 'y', 'n', 'skip', or 'quit'")
                    continue

            # Create label
            label = {
                'query': query,
                'doc_id': doc.get('doc_id', ''),
                'doc_url': doc.get('url', ''),
                'language': doc.get('language', 'unknown'),
                'relevant': relevant,
                'annotator': annotator,
                'timestamp': datetime.now().isoformat(),
                'model_used': model_used,
                'score': f"{score:.3f}"
            }

            self.labels.append(label)
            labels_created += 1

            print(f"   Labeled as: {relevant}\n")

        return labels_created

    def _save_labels(self):
        """Save labels to CSV file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

            with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
                if self.labels:
                    fieldnames = ['query', 'doc_id', 'doc_url', 'language', 'relevant', 'annotator']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    # Write only required fields
                    for label in self.labels:
                        writer.writerow({
                            'query': label['query'],
                            'doc_id': label.get('doc_id', ''),
                            'doc_url': label['doc_url'],
                            'language': label['language'],
                            'relevant': label['relevant'],
                            'annotator': label['annotator']
                        })

        except Exception as e:
            print(f"L Error saving labels: {e}")

    def get_statistics(self):
        """
        Get labeling statistics

        Returns:
            dict: Statistics about labels
        """
        if not self.labels:
            return {
                'total_labels': 0,
                'queries_labeled': 0,
                'relevant_count': 0,
                'not_relevant_count': 0
            }

        relevant_count = sum(1 for label in self.labels if label['relevant'] == 'yes')
        not_relevant_count = sum(1 for label in self.labels if label['relevant'] == 'no')
        queries = set(label['query'] for label in self.labels)

        return {
            'total_labels': len(self.labels),
            'queries_labeled': len(queries),
            'relevant_count': relevant_count,
            'not_relevant_count': not_relevant_count,
            'relevance_rate': relevant_count / len(self.labels) if self.labels else 0
        }

    def print_statistics(self):
        """Print labeling statistics"""
        stats = self.get_statistics()

        print(f"\n{'=' * 70}")
        print("Labeling Statistics")
        print(f"{'=' * 70}")
        print(f"Total labels: {stats['total_labels']}")
        print(f"Queries labeled: {stats['queries_labeled']}")
        print(f"Relevant: {stats['relevant_count']}")
        print(f"Not relevant: {stats['not_relevant_count']}")
        print(f"Relevance rate: {stats['relevance_rate']:.1%}")
        print(f"{'=' * 70}\n")


if __name__ == "__main__":
    # Test the labeling tool
    print("Testing RelevanceLabelingTool...")

    # Mock data
    test_queries = ['cricket', 'education']
    test_results = {
        'cricket': {
            'Semantic': [
                {
                    'doc': {
                        'doc_id': 'doc1',
                        'title': 'Bangladesh Cricket News',
                        'body': 'Bangladesh cricket team won the match...',
                        'url': 'http://example.com/cricket1',
                        'language': 'english'
                    },
                    'score': 0.92
                },
                {
                    'doc': {
                        'doc_id': 'doc2',
                        'title': 'Sports Update',
                        'body': 'Latest sports news...',
                        'url': 'http://example.com/sports',
                        'language': 'english'
                    },
                    'score': 0.75
                }
            ]
        },
        'education': {
            'Semantic': [
                {
                    'doc': {
                        'doc_id': 'doc5',
                        'title': 'Education System',
                        'body': 'Bangladesh education system...',
                        'url': 'http://example.com/edu',
                        'language': 'english'
                    },
                    'score': 0.88
                }
            ]
        }
    }

    # Create tool
    tool = RelevanceLabelingTool(
        queries=test_queries,
        retrieval_results=test_results,
        output_file='test_labels.csv'
    )

    print("\n RelevanceLabelingTool initialized successfully!")
    print("Note: Interactive labeling requires user input, skipping in test mode")

    # Cleanup
    if os.path.exists('test_labels.csv'):
        os.remove('test_labels.csv')
