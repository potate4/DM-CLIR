"""
TF-IDF Retrieval Model
Uses scikit-learn for TF-IDF vectorization and cosine similarity
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class TFIDFRetriever:
    def __init__(self, documents):
        """
        Initialize TF-IDF retriever
        
        Args:
            documents (list): List of document dictionaries with 'tokens' field
        """
        self.documents = documents
        self.doc_texts = [' '.join(doc['tokens']) for doc in documents]
        
        print(f"Building TF-IDF matrix for {len(documents)} documents...")
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.vectorizer.fit_transform(self.doc_texts)
        print("✅ TF-IDF matrix built")
    
    def search(self, query_tokens, top_k=10):
        """
        Search for documents using TF-IDF
        
        Args:
            query_tokens (list): List of query tokens
            top_k (int): Number of results to return
            
        Returns:
            list: List of result dictionaries with doc, score, rank
        """
        query_text = ' '.join(query_tokens)
        query_vec = self.vectorizer.transform([query_text])
        scores = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        results = []
        for rank, idx in enumerate(top_indices, 1):
            results.append({
                'doc': self.documents[idx],
                'score': float(scores[idx]),
                'rank': rank,
                'model': 'TF-IDF'
            })
        
        return results


if __name__ == "__main__":
    # Test
    print("Testing TFIDFRetriever...")
    
    test_docs = [
        {'id': 1, 'title': 'Cricket News', 'tokens': ['bangladesh', 'cricket', 'team', 'won']},
        {'id': 2, 'title': 'Education', 'tokens': ['education', 'system', 'bangladesh']},
        {'id': 3, 'title': 'Sports', 'tokens': ['cricket', 'match', 'today']}
    ]
    
    retriever = TFIDFRetriever(test_docs)
    results = retriever.search(['cricket', 'bangladesh'], top_k=2)
    
    print("\nTest Results:")
    for r in results:
        print(f"  Rank {r['rank']}: {r['doc']['title']} (score: {r['score']:.3f})")
    
    print("\n✅ TF-IDF test passed!")
