"""
Document Ranker
Normalizes scores from different retrieval models to [0, 1] scale and ranks documents
"""

import numpy as np


class DocumentRanker:
    """
    Unified ranking interface for all retrieval models
    Ensures all scores are normalized to [0, 1] scale
    """

    def __init__(self):
        """Initialize the document ranker"""
        self.normalization_methods = {
            'BM25': self._normalize_max,
            'TF-IDF': self._normalize_max,
            'Fuzzy': self._normalize_fuzzy,
            'Semantic': self._normalize_semantic
        }

    def rank_documents(self, results, model_name, top_k=10):
        """
        Rank and normalize scores for a model's results

        Args:
            results (list): List of result dicts from retrieval model
                Each result should have: {'doc': {...}, 'score': float, 'rank': int}
            model_name (str): Name of the model ('BM25', 'TF-IDF', 'Fuzzy', 'Semantic')
            top_k (int): Number of top results to return

        Returns:
            dict: Ranked results with normalized scores
                {
                    'query': str (if available in results),
                    'model': str,
                    'top_k': int,
                    'results': [
                        {
                            'rank': 1,
                            'doc': {...},
                            'score': 0.85,        # Normalized [0, 1]
                            'raw_score': 12.5,    # Original score
                        },
                        ...
                    ]
                }
        """
        if not results:
            return {
                'model': model_name,
                'top_k': top_k,
                'results': []
            }

        # Extract scores
        scores = [r.get('score', r.get('raw_score', 0)) for r in results]
        raw_scores = [r.get('raw_score', r.get('score', 0)) for r in results]

        # Normalize scores
        if model_name in self.normalization_methods:
            normalized_scores = self.normalization_methods[model_name](scores)
        else:
            # Default: assume already normalized
            normalized_scores = scores

        # Create ranked results
        ranked_results = []
        for i, result in enumerate(results[:top_k]):
            ranked_results.append({
                'rank': i + 1,
                'doc': result['doc'],
                'score': float(normalized_scores[i]),
                'raw_score': float(raw_scores[i]),
                'model': model_name
            })

        return {
            'model': model_name,
            'top_k': top_k,
            'results': ranked_results
        }

    def _normalize_max(self, scores):
        """
        Max normalization: divide all scores by max score
        Used for BM25 and TF-IDF

        Args:
            scores (list): Raw scores

        Returns:
            list: Normalized scores [0, 1]
        """
        if not scores:
            return []

        max_score = max(scores)
        if max_score == 0:
            return [0.0] * len(scores)

        return [score / max_score for score in scores]

    def _normalize_fuzzy(self, scores):
        """
        Fuzzy normalization: scores are [0, 100], divide by 100

        Args:
            scores (list): Fuzzy scores [0, 100]

        Returns:
            list: Normalized scores [0, 1]
        """
        return [score / 100.0 for score in scores]

    def _normalize_semantic(self, scores):
        """
        Semantic normalization: cosine similarity is already [0, 1] after processing
        (SemanticRetriever already normalizes from [-1, 1] to [0, 1])

        Args:
            scores (list): Semantic scores (already normalized)

        Returns:
            list: Scores as-is (already [0, 1])
        """
        # Already normalized by SemanticRetriever
        return scores

    def merge_rankings(self, all_results, weights=None):
        """
        Merge rankings from multiple models using weighted fusion

        Args:
            all_results (dict): Results from multiple models
                {
                    'BM25': {'results': [...]},
                    'Semantic': {'results': [...]},
                    ...
                }
            weights (dict): Weights for each model (default: equal weights)
                {
                    'BM25': 0.25,
                    'TF-IDF': 0.25,
                    'Fuzzy': 0.2,
                    'Semantic': 0.3
                }

        Returns:
            list: Merged and re-ranked results
        """
        if weights is None:
            # Default weights: semantic gets highest for cross-lingual
            weights = {
                'BM25': 0.3,
                'TF-IDF': 0.2,
                'Fuzzy': 0.2,
                'Semantic': 0.3
            }

        # Create a dictionary to aggregate scores by doc_id
        doc_scores = {}

        for model_name, results in all_results.items():
            if model_name not in weights:
                continue

            weight = weights[model_name]

            for result in results.get('results', []):
                doc_id = result['doc'].get('doc_id', result['doc'].get('url', ''))

                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {
                        'doc': result['doc'],
                        'weighted_score': 0.0,
                        'model_scores': {}
                    }

                doc_scores[doc_id]['weighted_score'] += result['score'] * weight
                doc_scores[doc_id]['model_scores'][model_name] = result['score']

        # Sort by weighted score
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1]['weighted_score'],
            reverse=True
        )

        # Create ranked results
        merged_results = []
        for rank, (doc_id, data) in enumerate(sorted_docs, 1):
            merged_results.append({
                'rank': rank,
                'doc': data['doc'],
                'score': data['weighted_score'],
                'model_scores': data['model_scores'],
                'model': 'Hybrid'
            })

        return merged_results


if __name__ == "__main__":
    # Test the ranker
    print("Testing DocumentRanker...")

    # Sample results from BM25
    bm25_results = [
        {'doc': {'title': 'Doc 1', 'doc_id': '1'}, 'score': 12.5, 'rank': 1},
        {'doc': {'title': 'Doc 2', 'doc_id': '2'}, 'score': 8.3, 'rank': 2},
        {'doc': {'title': 'Doc 3', 'doc_id': '3'}, 'score': 5.0, 'rank': 3}
    ]

    # Sample results from Semantic
    semantic_results = [
        {'doc': {'title': 'Doc 1', 'doc_id': '1'}, 'score': 0.92, 'rank': 1},
        {'doc': {'title': 'Doc 2', 'doc_id': '2'}, 'score': 0.85, 'rank': 2},
        {'doc': {'title': 'Doc 3', 'doc_id': '3'}, 'score': 0.75, 'rank': 3}
    ]

    ranker = DocumentRanker()

    # Test BM25 ranking
    print("\nBM25 Results (normalized):")
    bm25_ranked = ranker.rank_documents(bm25_results, 'BM25', top_k=3)
    for r in bm25_ranked['results']:
        print(f"  {r['rank']}. [{r['score']:.3f}] {r['doc']['title']} (raw: {r['raw_score']:.2f})")

    # Test Semantic ranking
    print("\nSemantic Results (normalized):")
    semantic_ranked = ranker.rank_documents(semantic_results, 'Semantic', top_k=3)
    for r in semantic_ranked['results']:
        print(f"  {r['rank']}. [{r['score']:.3f}] {r['doc']['title']}")

    # Test hybrid ranking
    print("\nHybrid Results (weighted fusion):")
    all_results = {
        'BM25': bm25_ranked,
        'Semantic': semantic_ranked
    }
    hybrid = ranker.merge_rankings(all_results)
    for r in hybrid[:3]:
        print(f"  {r['rank']}. [{r['score']:.3f}] {r['doc']['title']}")
        print(f"     BM25: {r['model_scores'].get('BM25', 0):.3f}, Semantic: {r['model_scores'].get('Semantic', 0):.3f}")

    print("\n DocumentRanker test passed!")
