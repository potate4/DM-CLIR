"""
Semantic Retrieval Model
Uses sentence-transformers for multilingual semantic embeddings
"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pickle
import os


class SemanticRetriever:
    def __init__(self, documents, model_name='sentence-transformers/LaBSE', cache_file='embeddings_cache.pkl'):
        """
        Initialize Semantic retriever
        
        Args:
            documents (list): List of document dictionaries
            model_name (str): Name of sentence-transformer model
            cache_file (str): Path to cache embeddings
        """
        self.documents = documents
        self.model_name = model_name
        self.cache_file = cache_file
        
        print(f"Loading {model_name} model...")
        self.model = SentenceTransformer(model_name)
        print("✅ Model loaded")
        
        # Load or compute embeddings
        if os.path.exists(cache_file):
            print(f"Loading cached embeddings from {cache_file}...")
            with open(cache_file, 'rb') as f:
                self.embeddings = pickle.load(f)
            print(f"✅ Loaded {len(self.embeddings)} cached embeddings")
        else:
            print(f"Computing embeddings for {len(documents)} documents...")
            self.embeddings = self._encode_documents()
            # Save cache
            with open(cache_file, 'wb') as f:
                pickle.dump(self.embeddings, f)
            print(f"✅ Embeddings cached to {cache_file}")
    
    def _encode_documents(self):
        """Encode all documents"""
        texts = []
        for doc in self.documents:
            text = f"{doc.get('title', '')} {doc.get('body', '')[:500]}"
            texts.append(text)
        
        embeddings = self.model.encode(
            texts,
            batch_size=64,
            show_progress_bar=True,
            convert_to_numpy=True,
            device='cuda'  # Use GPU
        )
        return embeddings
    
    def search(self, query, top_k=10):
        """
        Search for documents using semantic similarity
        
        Args:
            query (str): Query string
            top_k (int): Number of results to return
            
        Returns:
            list: List of result dictionaries with doc, score, rank
        """
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        scores = cosine_similarity(query_embedding, self.embeddings)[0]
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        results = []
        for rank, idx in enumerate(top_indices, 1):
            # Normalize cosine similarity from [-1, 1] to [0, 1]
            normalized_score = (scores[idx] + 1) / 2
            
            results.append({
                'doc': self.documents[idx],
                'score': float(normalized_score),
                'cosine_score': float(scores[idx]),
                'rank': rank,
                'model': 'Semantic'
            })
        
        return results


if __name__ == "__main__":
    # Test
    print("Testing SemanticRetriever...")
    
    test_docs = [
        {'id': 1, 'title': 'Cricket News', 'body': 'Bangladesh cricket team won the match'},
        {'id': 2, 'title': 'Education System', 'body': 'Education system in Bangladesh needs reform'},
        {'id': 3, 'title': 'Sports Update', 'body': 'Cricket match scheduled for today'}
    ]
    
    retriever = SemanticRetriever(test_docs, cache_file='test_embeddings.pkl')
    results = retriever.search('cricket bangladesh', top_k=2)
    
    print("\nTest Results:")
    for r in results:
        print(f"  Rank {r['rank']}: {r['doc']['title']} (score: {r['score']:.3f})")
    
    print("\n✅ Semantic test passed!")
    
    # Cleanup test cache
    if os.path.exists('test_embeddings.pkl'):
        os.remove('test_embeddings.pkl')
