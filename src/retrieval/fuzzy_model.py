"""
Fuzzy Matching Retrieval Model
Uses fuzzywuzzy for fuzzy string matching and transliteration handling
"""

from fuzzywuzzy import fuzz
import numpy as np


class FuzzyRetriever:
    def __init__(self, documents):
        """
        Initialize Fuzzy retriever
        
        Args:
            documents (list): List of document dictionaries
        """
        self.documents = documents
        self.doc_texts = []
        
        print(f"Building fuzzy search index for {len(documents)} documents...")
        for doc in documents:
            text = f"{doc.get('title', '')} {doc.get('body', '')}"
            self.doc_texts.append(text.lower())
        print("✅ Fuzzy index built")
    
    def search(self, query, top_k=10):
        """
        Search for documents using fuzzy matching
        
        Args:
            query (str): Query string (not tokenized)
            top_k (int): Number of results to return
            
        Returns:
            list: List of result dictionaries with doc, score, rank
        """
        query_lower = query.lower()
        scores = [fuzz.partial_ratio(query_lower, text) for text in self.doc_texts]
        scores = np.array(scores)
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        results = []
        for rank, idx in enumerate(top_indices, 1):
            results.append({
                'doc': self.documents[idx],
                'score': float(scores[idx]) / 100.0,  # Normalize to [0, 1]
                'raw_score': int(scores[idx]),
                'rank': rank,
                'model': 'Fuzzy'
            })
        
        return results


if __name__ == "__main__":
    # Test
    print("Testing FuzzyRetriever...")
    
    test_docs = [
        {'id': 1, 'title': 'Cricket News', 'body': 'Bangladesh cricket team won'},
        {'id': 2, 'title': 'Education', 'body': 'Education system in Bangladesh'},
        {'id': 3, 'title': 'Sports', 'body': 'Cricket match today'}
    ]
    
    retriever = FuzzyRetriever(test_docs)
    results = retriever.search('cricket bangladesh', top_k=2)
    
    print("\nTest Results:")
    for r in results:
        print(f"  Rank {r['rank']}: {r['doc']['title']} (score: {r['score']:.3f})")
    
    print("\n✅ Fuzzy test passed!")
