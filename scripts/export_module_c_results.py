"""
Export Module C Results to Multiple Formats
Creates JSON, CSV, and HTML reports
"""

import sys
import os
import json
import csv
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.retrieval import BM25Retriever, TFIDFRetriever, FuzzyRetriever, SemanticRetriever


def load_documents_safe(filepath):
    """Safely load documents"""
    documents = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            documents = json.load(f)
    except json.JSONDecodeError:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        documents.append(json.loads(line))
                    except:
                        continue
    
    return documents


def save_results_json(results, filename='module_c_results.json'):
    """Save results as JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved JSON to {filename}")


def save_results_csv(results, filename='module_c_results.csv'):
    """Save results as CSV"""
    rows = []
    
    for query_result in results:
        query = query_result['query']
        
        for model_name in ['BM25', 'TF-IDF', 'Fuzzy', 'Semantic']:
            if model_name in query_result:
                for result in query_result[model_name]:
                    rows.append({
                        'query': query,
                        'model': model_name,
                        'rank': result['rank'],
                        'score': result['score'],
                        'doc_id': result['doc'].get('id', 'N/A'),
                        'doc_title': result['doc'].get('title', 'N/A'),
                        'doc_language': result['doc'].get('language', 'N/A')
                    })
    
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    
    print(f"✅ Saved CSV to {filename}")


def save_results_html(results, filename='module_c_results.html'):
    """Save results as HTML report"""
    html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Module C - Retrieval Results</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        .query-section {
            background: white;
            margin: 20px 0;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .query-title {
            font-size: 20px;
            font-weight: bold;
            color: #2196F3;
            margin-bottom: 15px;
        }
        .model-section {
            margin: 15px 0;
        }
        .model-name {
            font-size: 16px;
            font-weight: bold;
            color: #555;
            background: #f0f0f0;
            padding: 8px;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .result-item {
            padding: 8px;
            margin: 5px 0;
            border-left: 3px solid #4CAF50;
            padding-left: 15px;
        }
        .rank {
            font-weight: bold;
            color: #FF9800;
        }
        .score {
            background: #E3F2FD;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
        }
        .doc-title {
            color: #333;
            margin-left: 10px;
        }
        .metadata {
            background: #FFF9C4;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #4CAF50;
            color: white;
        }
    </style>
</head>
<body>
    <h1>📊 Module C - Cross-Lingual Retrieval Results</h1>
    
    <div class="metadata">
        <strong>Generated:</strong> {timestamp}<br>
        <strong>Total Queries:</strong> {num_queries}<br>
        <strong>Models Tested:</strong> BM25, TF-IDF, Fuzzy Matching, Semantic Embeddings<br>
        <strong>Documents:</strong> {num_docs}
    </div>
"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    num_queries = len(results)
    num_docs = results[0].get('num_documents', 'N/A') if results else 0
    
    html = html.format(timestamp=timestamp, num_queries=num_queries, num_docs=num_docs)
    
    # Add each query's results
    for query_result in results:
        query = query_result['query']
        
        html += f"""
    <div class="query-section">
        <div class="query-title">🔍 Query: "{query}"</div>
"""
        
        for model_name in ['BM25', 'TF-IDF', 'Fuzzy', 'Semantic']:
            if model_name in query_result:
                html += f"""
        <div class="model-section">
            <div class="model-name">{model_name}</div>
"""
                
                for result in query_result[model_name]:
                    rank = result['rank']
                    score = result['score']
                    title = result['doc'].get('title', 'No title')
                    
                    html += f"""
            <div class="result-item">
                <span class="rank">{rank}.</span>
                <span class="score">{score:.3f}</span>
                <span class="doc-title">{title}</span>
            </div>
"""
                
                html += """
        </div>
"""
        
        html += """
    </div>
"""
    
    html += """
</body>
</html>
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Saved HTML to {filename}")


def create_comparison_table(results, filename='model_comparison.csv'):
    """Create model comparison table"""
    rows = []
    
    for query_result in results:
        query = query_result['query']
        
        # Calculate average scores per model
        model_scores = {}
        for model_name in ['BM25', 'TF-IDF', 'Fuzzy', 'Semantic']:
            if model_name in query_result:
                scores = [r['score'] for r in query_result[model_name]]
                avg_score = sum(scores) / len(scores) if scores else 0
                model_scores[model_name] = avg_score
        
        rows.append({
            'query': query,
            'BM25_avg_score': model_scores.get('BM25', 0),
            'TFIDF_avg_score': model_scores.get('TF-IDF', 0),
            'Fuzzy_avg_score': model_scores.get('Fuzzy', 0),
            'Semantic_avg_score': model_scores.get('Semantic', 0)
        })
    
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    
    print(f"✅ Saved comparison table to {filename}")


def main():
    """Main execution"""
    print("="*80)
    print("Module C - Results Exporter")
    print("="*80)
    
    # Load documents
    print("\n📥 Loading documents...")
    doc_paths = [
        'all_documents_clean.json',
        'data/processed/english_docs.json',
        'data/processed/bangla_docs.json'
    ]
    
    documents = []
    for path in doc_paths:
        if os.path.exists(path):
            docs = load_documents_safe(path)
            documents.extend(docs)
            print(f"  ✅ Loaded {len(docs)} from {path}")
    
    if not documents:
        print("  ⚠️ No documents found!")
        return
    
    # Ensure tokens
    for doc in documents:
        if 'tokens' not in doc or not doc['tokens']:
            text = (doc.get('title', '') + ' ' + doc.get('body', '')).lower()
            doc['tokens'] = [w for w in text.split() if len(w) > 1]
    
    print(f"\n📊 Total documents: {len(documents)}")
    
    # Initialize models
    print("\n🔨 Building retrieval models...")
    bm25 = BM25Retriever(documents)
    tfidf = TFIDFRetriever(documents)
    fuzzy = FuzzyRetriever(documents)
    semantic = SemanticRetriever(documents, cache_file='data/embeddings_cache.pkl')
    
    # Test queries
    test_queries = [
        "bangladesh cricket team",
        "education system",
        "economic growth",
        "শিক্ষা ব্যবস্থা",
        "ক্রিকেট খেলা"
    ]
    
    # Collect results
    print("\n🔍 Running queries...")
    all_results = []
    
    for query in test_queries:
        print(f"  Processing: {query}")
        tokens = query.lower().split()
        
        result = {
            'query': query,
            'num_documents': len(documents),
            'BM25': bm25.search(tokens, top_k=10),
            'TF-IDF': tfidf.search(tokens, top_k=10),
            'Fuzzy': fuzzy.search(query, top_k=10),
            'Semantic': semantic.search(query, top_k=10)
        }
        
        all_results.append(result)
    
    # Export results
    print("\n💾 Exporting results...")
    save_results_json(all_results, 'module_c_results.json')
    save_results_csv(all_results, 'module_c_results.csv')
    save_results_html(all_results, 'module_c_results.html')
    create_comparison_table(all_results, 'model_comparison.csv')
    
    print("\n✅ All exports complete!")
    print("\nGenerated files:")
    print("  📄 module_c_results.json - Full results in JSON")
    print("  📊 module_c_results.csv - Results in CSV")
    print("  🌐 module_c_results.html - Interactive HTML report")
    print("  📈 model_comparison.csv - Model comparison table")


if __name__ == "__main__":
    main()
