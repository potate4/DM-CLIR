"""
Module C - Run All Retrieval Models
Complete implementation of all retrieval methods
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.retrieval import BM25Retriever, TFIDFRetriever, FuzzyRetriever, SemanticRetriever


class MultiModelRetrieval:
    """Unified interface for all retrieval models"""
    
    def __init__(self, documents):
        """
        Initialize all retrieval models
        
        Args:
            documents (list): List of document dictionaries
        """
        self.documents = documents
        
        print("="*80)
        print("Initializing All Retrieval Models")
        print("="*80)
        
        # Initialize models
        print("\n[1/4] Building BM25...")
        self.bm25 = BM25Retriever(documents)
        
        print("\n[2/4] Building TF-IDF...")
        self.tfidf = TFIDFRetriever(documents)
        
        print("\n[3/4] Building Fuzzy Matching...")
        self.fuzzy = FuzzyRetriever(documents)
        
        print("\n[4/4] Building Semantic Embeddings (this takes 1-5 minutes)...")
        self.semantic = SemanticRetriever(documents, cache_file='data/embeddings_cache.pkl')
        
        print("\n" + "="*80)
        print("✅ All models ready!")
        print("="*80)
    
    def search_all(self, query, top_k=10):
        """
        Search using all models
        
        Args:
            query (str): Query string
            top_k (int): Number of results per model
            
        Returns:
            dict: Results from all models
        """
        query_tokens = query.lower().split()
        
        results = {
            'query': query,
            'BM25': self.bm25.search(query_tokens, top_k),
            'TF-IDF': self.tfidf.search(query_tokens, top_k),
            'Fuzzy': self.fuzzy.search(query, top_k),
            'Semantic': self.semantic.search(query, top_k)
        }
        
        return results
    
    def compare(self, query, top_k=5):
        """Print comparison of all models"""
        results = self.search_all(query, top_k)
        
        print(f"\n{'='*80}")
        print(f"Query: '{query}'")
        print(f"{'='*80}\n")
        
        for model_name in ['BM25', 'TF-IDF', 'Fuzzy', 'Semantic']:
            print(f"{model_name} Results:")
            print("-" * 70)
            for r in results[model_name]:
                title = r['doc'].get('title', 'No title')[:60]
                print(f"  {r['rank']}. [{r['score']:.3f}] {title}")
            print()


def load_documents_safe(filepath):
    """Safely load documents from potentially corrupted JSON"""
    documents = []
    
    try:
        # Try normal JSON load first
        with open(filepath, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        print(f"  ✅ Loaded {len(documents)} documents from {filepath}")
    except json.JSONDecodeError:
        # File has multiple JSON objects - load line by line
        print(f"  ⚠️ File has multiple JSON objects, loading line by line...")
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        doc = json.loads(line)
                        documents.append(doc)
                    except json.JSONDecodeError:
                        continue
        print(f"  ✅ Loaded {len(documents)} documents from {filepath}")
    
    return documents


def main():
    """Main execution"""
    print("Module C - Retrieval Models")
    print("="*80)
    
    # Load documents
    print("\n📥 Loading documents...")
    
    # Try different locations
    doc_paths = [
        'data/processed/english_docs.json',
        'data/processed/bangla_docs.json',
        'all_documents.json'
    ]
    
    documents = []
    for path in doc_paths:
        if os.path.exists(path):
            docs = load_documents_safe(path)
            documents.extend(docs)
    
    if not documents:
        print("  ⚠️ No documents found. Creating test data...")
        documents = [
            {
                'id': i,
                'title': f'Test Document {i}',
                'body': 'Sample content about cricket, education, and economy in Bangladesh.',
                'tokens': ['test', 'document', 'cricket', 'education', 'economy', 'bangladesh'],
                'language': 'English' if i % 2 == 0 else 'Bangla'
            }
            for i in range(50)
        ]
        print(f"  ✅ Created {len(documents)} test documents")
    
    # Ensure all docs have tokens
    print("\n🔧 Preparing documents...")
    for doc in documents:
        if 'tokens' not in doc or not doc['tokens']:
            text = (doc.get('title', '') + ' ' + doc.get('body', '')).lower()
            doc['tokens'] = [w for w in text.split() if len(w) > 1]
    
    print(f"\n📊 Total documents: {len(documents)}")
    
    # Initialize retrieval system
    retrieval = MultiModelRetrieval(documents)
    
    # Test queries
    test_queries = [
        "bangladesh cricket team",
        "education system",
        "economic growth"
    ]
    
    print("\n🧪 Testing with sample queries:")
    for query in test_queries:
        retrieval.compare(query, top_k=3)
    
    print("\n✅ Module C Complete!")
    print(f"All retrieval models working with {len(documents)} documents")
    
    # Save results summary
    print("\n💾 Saving results...")
    summary = {
        'total_documents': len(documents),
        'models': ['BM25', 'TF-IDF', 'Fuzzy', 'Semantic'],
        'status': 'complete'
    }
    
    with open('module_c_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("  ✅ Summary saved to module_c_summary.json")


if __name__ == "__main__":
    main()
