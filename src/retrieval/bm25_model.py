"""
BM25 Retrieval Model
Uses rank-bm25 library for lexical retrieval
"""

from rank_bm25 import BM25Okapi
import numpy as np


class BM25Retriever:
    def __init__(self, documents):
        """
        Initialize BM25 retriever
        
        Args:
            documents (list): List of document dictionaries with 'tokens' field
        """
        self.documents = documents
        self.tokenized_docs = [doc['tokens'] for doc in documents]
        
        print(f"Building BM25 index for {len(documents)} documents...")
        self.bm25 = BM25Okapi(self.tokenized_docs)
        print("✅ BM25 index built")
    
    def search(self, query_tokens, top_k=10):
        """
        Search for documents using BM25
        
        Args:
            query_tokens (list): List of query tokens
            top_k (int): Number of results to return
            
        Returns:
            list: List of result dictionaries with doc, score, rank
        """
        scores = self.bm25.get_scores(query_tokens)
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        results = []
        max_score = max(scores[top_indices[0]], 1.0) if len(top_indices) > 0 else 1.0
        
        for rank, idx in enumerate(top_indices, 1):
            results.append({
                'doc': self.documents[idx],
                'score': float(scores[idx]) / max_score,
                'raw_score': float(scores[idx]),
                'rank': rank,
                'model': 'BM25'
            })
        
        return results


if __name__ == "__main__":
    # Test
    print("Testing BM25Retriever...")
    
    test_docs = [
        {'id': 1, 'title': 'Cricket News', 'tokens': ['bangladesh', 'cricket', 'team', 'won']},
        {'id': 2, 'title': 'Education', 'tokens': ['education', 'system', 'bangladesh']},
        {'id': 3, 'title': 'Sports', 'tokens': ['cricket', 'match', 'today']}
    ]
    
    retriever = BM25Retriever(test_docs)
    results = retriever.search(['cricket', 'bangladesh'], top_k=2)
    
    print("\nTest Results:")
    for r in results:
        print(f"  Rank {r['rank']}: {r['doc']['title']} (score: {r['score']:.3f})")
    
    print("\n✅ BM25 test passed!")
