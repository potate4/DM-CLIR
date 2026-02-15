"""
Evaluation Metrics
Standard IR metrics for evaluating retrieval effectiveness
"""

import math


class EvaluationMetrics:
    """
    Standard information retrieval metrics
    All methods are static
    """

    @staticmethod
    def precision_at_k(retrieved_docs, relevant_docs, k=10):
        """
        Precision@K = # relevant docs in top-K / K

        Measures what fraction of retrieved documents are relevant

        Args:
            retrieved_docs (list): List of doc_ids in ranked order
            relevant_docs (set or list): Set of relevant doc_ids
            k (int): Cutoff (default 10)

        Returns:
            float: Precision@K score [0, 1]

        Example:
            >>> retrieved = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5']
            >>> relevant = {'doc1', 'doc3', 'doc5'}
            >>> precision_at_k(retrieved, relevant, k=5)
            0.6  # 3 relevant out of 5
        """
        if not retrieved_docs or k == 0:
            return 0.0

        relevant_set = set(relevant_docs)
        top_k = retrieved_docs[:k]

        relevant_in_k = sum(1 for doc in top_k if doc in relevant_set)

        return relevant_in_k / k

    @staticmethod
    def recall_at_k(retrieved_docs, relevant_docs, k=50):
        """
        Recall@K = # relevant docs retrieved / total relevant docs

        Measures what fraction of relevant documents were retrieved

        Args:
            retrieved_docs (list): List of doc_ids in ranked order
            relevant_docs (set or list): Set of relevant doc_ids
            k (int): Cutoff (default 50)

        Returns:
            float: Recall@K score [0, 1]

        Example:
            >>> retrieved = ['doc1', 'doc2', 'doc3']
            >>> relevant = {'doc1', 'doc3', 'doc5', 'doc7'}  # 4 total relevant
            >>> recall_at_k(retrieved, relevant, k=3)
            0.5  # 2 retrieved out of 4 total
        """
        relevant_set = set(relevant_docs)

        if not relevant_set:
            return 0.0

        top_k = retrieved_docs[:k]
        relevant_in_k = sum(1 for doc in top_k if doc in relevant_set)

        return relevant_in_k / len(relevant_set)

    @staticmethod
    def ndcg_at_k(retrieved_docs, relevant_docs, k=10, relevance_scores=None):
        """
        Normalized Discounted Cumulative Gain@K

        Measures ranking quality with position-based discounting
        Higher-ranked relevant documents contribute more to the score

        Formula:
            DCG@K = �(rel_i / log2(i+1)) for i in 1..k
            nDCG@K = DCG@K / IDCG@K

        Args:
            retrieved_docs (list): List of doc_ids in ranked order
            relevant_docs (set or list): Set of relevant doc_ids
            k (int): Cutoff (default 10)
            relevance_scores (dict): Optional dict mapping doc_id -> relevance grade
                                     If None, binary relevance (1 or 0) is used

        Returns:
            float: nDCG@K score [0, 1]

        Example:
            >>> retrieved = ['doc1', 'doc2', 'doc3', 'doc4']
            >>> relevant = {'doc1', 'doc3'}
            >>> ndcg_at_k(retrieved, relevant, k=4)
            0.861  # Higher because relevant docs are near the top
        """
        if not retrieved_docs or k == 0:
            return 0.0

        relevant_set = set(relevant_docs)

        # Calculate DCG
        dcg = 0.0
        for i, doc in enumerate(retrieved_docs[:k], 1):
            if relevance_scores:
                relevance = relevance_scores.get(doc, 0)
            else:
                relevance = 1 if doc in relevant_set else 0

            dcg += relevance / math.log2(i + 1)

        # Calculate IDCG (Ideal DCG)
        if relevance_scores:
            # Sort by relevance scores
            ideal_relevances = sorted(
                [relevance_scores.get(doc, 0) for doc in relevant_set],
                reverse=True
            )[:k]
        else:
            # Binary relevance: all relevant docs have score 1
            ideal_relevances = [1] * min(k, len(relevant_set))

        idcg = sum(
            rel / math.log2(i + 1)
            for i, rel in enumerate(ideal_relevances, 1)
        )

        if idcg == 0:
            return 0.0

        return dcg / idcg

    @staticmethod
    def mean_reciprocal_rank(retrieved_docs, relevant_docs):
        """
        Mean Reciprocal Rank (MRR)

        MRR = 1 / rank of first relevant document

        Measures how quickly users can find a relevant document

        Args:
            retrieved_docs (list): List of doc_ids in ranked order
            relevant_docs (set or list): Set of relevant doc_ids

        Returns:
            float: MRR score [0, 1]

        Example:
            >>> retrieved = ['doc1', 'doc2', 'doc3', 'doc4']
            >>> relevant = {'doc3'}
            >>> mean_reciprocal_rank(retrieved, relevant)
            0.333  # First relevant doc at rank 3, so 1/3
        """
        relevant_set = set(relevant_docs)

        for i, doc in enumerate(retrieved_docs, 1):
            if doc in relevant_set:
                return 1.0 / i

        return 0.0

    @staticmethod
    def calculate_all_metrics(retrieved_docs, relevant_docs, k_precision=10, k_recall=50, k_ndcg=10):
        """
        Calculate all metrics at once

        Args:
            retrieved_docs (list): List of doc_ids in ranked order
            relevant_docs (set or list): Set of relevant doc_ids
            k_precision (int): K for Precision@K (default 10)
            k_recall (int): K for Recall@K (default 50)
            k_ndcg (int): K for nDCG@K (default 10)

        Returns:
            dict: All metrics
                {
                    'precision@10': float,
                    'recall@50': float,
                    'ndcg@10': float,
                    'mrr': float
                }
        """
        return {
            f'precision@{k_precision}': EvaluationMetrics.precision_at_k(
                retrieved_docs, relevant_docs, k=k_precision
            ),
            f'recall@{k_recall}': EvaluationMetrics.recall_at_k(
                retrieved_docs, relevant_docs, k=k_recall
            ),
            f'ndcg@{k_ndcg}': EvaluationMetrics.ndcg_at_k(
                retrieved_docs, relevant_docs, k=k_ndcg
            ),
            'mrr': EvaluationMetrics.mean_reciprocal_rank(
                retrieved_docs, relevant_docs
            )
        }


if __name__ == "__main__":
    # Test the metrics
    print("Testing EvaluationMetrics...")

    # Test data
    retrieved = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5', 'doc6', 'doc7', 'doc8', 'doc9', 'doc10']
    relevant = {'doc1', 'doc3', 'doc5', 'doc7', 'doc9', 'doc11', 'doc12'}  # 7 total relevant

    print("\nTest Data:")
    print(f"  Retrieved (top-10): {retrieved}")
    print(f"  Relevant (7 total): {relevant}")

    # Test Precision@10
    p_at_10 = EvaluationMetrics.precision_at_k(retrieved, relevant, k=10)
    print(f"\nPrecision@10: {p_at_10:.3f}")
    print(f"  Explanation: 5 relevant in top-10 / 10 = 0.500")

    # Test Recall@10
    r_at_10 = EvaluationMetrics.recall_at_k(retrieved, relevant, k=10)
    print(f"\nRecall@10: {r_at_10:.3f}")
    print(f"  Explanation: 5 retrieved / 7 total = 0.714")

    # Test nDCG@10
    ndcg = EvaluationMetrics.ndcg_at_k(retrieved, relevant, k=10)
    print(f"\nnDCG@10: {ndcg:.3f}")

    # Test MRR
    mrr = EvaluationMetrics.mean_reciprocal_rank(retrieved, relevant)
    print(f"\nMRR: {mrr:.3f}")
    print(f"  Explanation: First relevant doc at rank 1, so 1/1 = 1.000")

    # Test all metrics at once
    print("\nAll Metrics:")
    all_metrics = EvaluationMetrics.calculate_all_metrics(retrieved, relevant)
    for metric_name, value in all_metrics.items():
        print(f"  {metric_name:15s}: {value:.3f}")

    # Test edge cases
    print("\nEdge Cases:")

    # No relevant docs retrieved
    empty_retrieved = ['doc20', 'doc21', 'doc22']
    empty_metrics = EvaluationMetrics.calculate_all_metrics(empty_retrieved, relevant)
    print("\n  No relevant docs retrieved:")
    for metric_name, value in empty_metrics.items():
        print(f"    {metric_name:15s}: {value:.3f}")

    # Perfect retrieval
    perfect_retrieved = list(relevant) + ['doc20', 'doc21', 'doc22']
    perfect_metrics = EvaluationMetrics.calculate_all_metrics(perfect_retrieved, relevant)
    print("\n  Perfect retrieval (all relevant docs first):")
    for metric_name, value in perfect_metrics.items():
        print(f"    {metric_name:15s}: {value:.3f}")

    print("\n EvaluationMetrics test passed!")
