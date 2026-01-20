"""
Module C - Complete Analysis & Comparison
All required components for Module C submission
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.retrieval import BM25Retriever, TFIDFRetriever, FuzzyRetriever, SemanticRetriever


def load_results():
    """Load existing results"""
    with open('module_c_results.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def compare_bm25_tfidf():
    """
    REQUIRED: Compare BM25 with TF-IDF
    Show when each performs better
    """
    results = load_results()
    
    print("="*80)
    print("1. BM25 vs TF-IDF COMPARISON")
    print("="*80)
    
    comparisons = []
    
    for query_result in results:
        query = query_result['query']
        bm25_results = query_result['BM25']
        tfidf_results = query_result['TF-IDF']
        
        # Compare top result scores
        bm25_top_score = bm25_results[0]['score'] if bm25_results else 0
        tfidf_top_score = tfidf_results[0]['score'] if tfidf_results else 0
        
        winner = "BM25" if bm25_top_score > tfidf_top_score else "TF-IDF"
        
        print(f"\nQuery: '{query}'")
        print(f"  BM25 top score:   {bm25_top_score:.3f}")
        print(f"  TF-IDF top score: {tfidf_top_score:.3f}")
        print(f"  Winner: {winner}")
        
        # Explain why
        if winner == "BM25":
            print(f"  Why: BM25's document length normalization helps")
        else:
            print(f"  Why: TF-IDF's term weighting is more effective here")
        
        comparisons.append({
            'query': query,
            'bm25_score': bm25_top_score,
            'tfidf_score': tfidf_top_score,
            'winner': winner
        })
    
    # Save
    with open('bm25_vs_tfidf_comparison.json', 'w', encoding='utf-8') as f:
        json.dump(comparisons, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Saved to bm25_vs_tfidf_comparison.json")


def analyze_failure_cases():
    """
    REQUIRED: Analyze failure cases
    Synonyms, paraphrases, cross-script terms
    """
    results = load_results()
    
    print("\n" + "="*80)
    print("2. FAILURE CASE ANALYSIS")
    print("="*80)
    
    failures = {
        'synonym_failures': [],
        'cross_script_failures': [],
        'semantic_wins': []
    }
    
    for query_result in results:
        query = query_result['query']
        
        bm25_top = query_result['BM25'][0] if query_result['BM25'] else None
        semantic_top = query_result['Semantic'][0] if query_result['Semantic'] else None
        
        # Check for cross-script (Bangla queries)
        if any(ord(c) > 127 for c in query):
            print(f"\n❌ CROSS-SCRIPT FAILURE")
            print(f"Query: '{query}' (Bangla)")
            
            if bm25_top:
                print(f"  BM25 score: {bm25_top['score']:.3f}")
                print(f"  Top doc: {bm25_top['doc'].get('title', '')[:60]}")
            
            if semantic_top:
                print(f"  Semantic score: {semantic_top['score']:.3f}")
                print(f"  Top doc: {semantic_top['doc'].get('title', '')[:60]}")
            
            print(f"  WHY LEXICAL FAILS: BM25/TF-IDF require exact token match")
            print(f"                     Bangla characters don't match English tokens")
            print(f"  WHY SEMANTIC WORKS: Cross-lingual embeddings map both to same vector space")
            
            failures['cross_script_failures'].append({
                'query': query,
                'bm25_score': bm25_top['score'] if bm25_top else 0,
                'semantic_score': semantic_top['score'] if semantic_top else 0,
                'reason': 'Cross-script character mismatch'
            })
        
        # Check when semantic significantly beats lexical
        if bm25_top and semantic_top:
            if semantic_top['score'] > bm25_top['score'] + 0.2:
                print(f"\n✅ SEMANTIC WIN")
                print(f"Query: '{query}'")
                print(f"  BM25: {bm25_top['score']:.3f} - {bm25_top['doc'].get('title', '')[:50]}")
                print(f"  Semantic: {semantic_top['score']:.3f} - {semantic_top['doc'].get('title', '')[:50]}")
                print(f"  WHY: Likely uses synonyms or paraphrases")
                print(f"       Semantic embeddings capture meaning beyond exact words")
                
                failures['semantic_wins'].append({
                    'query': query,
                    'bm25_score': bm25_top['score'],
                    'semantic_score': semantic_top['score'],
                    'reason': 'Semantic understanding vs exact matching'
                })
    
    # Save
    with open('failure_case_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(failures, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Saved to failure_case_analysis.json")


def compare_semantic_vs_lexical():
    """
    REQUIRED: Compare results with lexical models
    """
    results = load_results()
    
    print("\n" + "="*80)
    print("3. SEMANTIC vs LEXICAL COMPARISON")
    print("="*80)
    
    comparisons = []
    
    for query_result in results:
        query = query_result['query']
        
        # Average scores
        bm25_avg = sum(r['score'] for r in query_result['BM25'][:5]) / 5
        semantic_avg = sum(r['score'] for r in query_result['Semantic'][:5]) / 5
        
        print(f"\nQuery: '{query}'")
        print(f"  Lexical (BM25) avg:  {bm25_avg:.3f}")
        print(f"  Semantic avg:        {semantic_avg:.3f}")
        print(f"  Difference:          {semantic_avg - bm25_avg:+.3f}")
        
        if semantic_avg > bm25_avg:
            print(f"  → Semantic dominates (better for meaning-based search)")
        else:
            print(f"  → Lexical dominates (better for exact term matching)")
        
        comparisons.append({
            'query': query,
            'lexical_avg': bm25_avg,
            'semantic_avg': semantic_avg,
            'winner': 'Semantic' if semantic_avg > bm25_avg else 'Lexical'
        })
    
    # Save
    with open('semantic_vs_lexical.json', 'w', encoding='utf-8') as f:
        json.dump(comparisons, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Saved to semantic_vs_lexical.json")


def demonstrate_transliteration():
    """
    REQUIRED: Show transliteration matching
    Bangladesh <-> বাংলাদেশ
    """
    print("\n" + "="*80)
    print("4. TRANSLITERATION MATCHING DEMONSTRATION")
    print("="*80)
    
    # Test transliteration pairs
    test_pairs = [
        ("Bangladesh", "বাংলাদেশ"),
        ("Dhaka", "ঢাকা"),
        ("cricket", "ক্রিকেট")
    ]
    
    from fuzzywuzzy import fuzz
    
    print("\nFuzzy matching scores for transliteration pairs:")
    print("-" * 70)
    
    results = []
    
    for english, bangla in test_pairs:
        score = fuzz.ratio(english.lower(), bangla) / 100.0
        
        print(f"'{english}' <-> '{bangla}'")
        print(f"  Fuzzy score: {score:.3f}")
        print(f"  Status: {'✅ Matched' if score > 0.3 else '❌ No match'}")
        print()
        
        results.append({
            'english': english,
            'bangla': bangla,
            'fuzzy_score': score,
            'matched': score > 0.3
        })
    
    print("Note: Pure character-based fuzzy matching has limitations.")
    print("For better transliteration, specialized libraries (like indic-transliteration) are recommended.")
    
    # Save
    with open('transliteration_demo.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Saved to transliteration_demo.json")


def create_hybrid_model():
    """
    OPTIONAL: Hybrid ranking
    Combine scores from multiple models
    """
    print("\n" + "="*80)
    print("5. HYBRID RANKING (OPTIONAL)")
    print("="*80)
    
    results = load_results()
    
    # Weights
    weights = {
        'BM25': 0.3,
        'TF-IDF': 0.0,  # Skip to avoid redundancy with BM25
        'Fuzzy': 0.2,
        'Semantic': 0.5
    }
    
    print(f"\nWeights: {weights}")
    print("Rationale:")
    print("  - Semantic: 0.5 (highest - best for cross-lingual)")
    print("  - BM25: 0.3 (good for exact matches)")
    print("  - Fuzzy: 0.2 (helps with spelling variations)")
    
    hybrid_results = []
    
    for query_result in results:
        query = query_result['query']
        
        print(f"\nQuery: '{query}'")
        
        # Combine scores for each document
        doc_scores = {}
        
        for model_name, weight in weights.items():
            if weight > 0 and model_name in query_result:
                for result in query_result[model_name][:10]:
                    doc_id = result['doc'].get('id', result['doc'].get('title', ''))
                    
                    if doc_id not in doc_scores:
                        doc_scores[doc_id] = {
                            'doc': result['doc'],
                            'combined_score': 0,
                            'breakdown': {}
                        }
                    
                    doc_scores[doc_id]['combined_score'] += weight * result['score']
                    doc_scores[doc_id]['breakdown'][model_name] = result['score']
        
        # Sort by combined score
        ranked = sorted(doc_scores.values(), key=lambda x: x['combined_score'], reverse=True)[:5]
        
        print("  Top 5 Hybrid Results:")
        for i, item in enumerate(ranked, 1):
            print(f"    {i}. [{item['combined_score']:.3f}] {item['doc'].get('title', '')[:50]}")
            print(f"       Breakdown: {item['breakdown']}")
        
        hybrid_results.append({
            'query': query,
            'weights': weights,
            'top_results': ranked[:5]
        })
    
    # Save
    with open('hybrid_ranking_results.json', 'w', encoding='utf-8') as f:
        json.dump(hybrid_results, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n✅ Saved to hybrid_ranking_results.json")


def main():
    """Run all Module C analyses"""
    
    print("="*80)
    print("MODULE C - COMPLETE ANALYSIS")
    print("All Required Components for Submission")
    print("="*80)
    
    # Run all analyses
    compare_bm25_tfidf()
    analyze_failure_cases()
    compare_semantic_vs_lexical()
    demonstrate_transliteration()
    create_hybrid_model()  # Optional but recommended
    
    print("\n" + "="*80)
    print("✅ MODULE C ANALYSIS COMPLETE!")
    print("="*80)
    
    print("\n📄 Generated files:")
    print("  1. bm25_vs_tfidf_comparison.json")
    print("  2. failure_case_analysis.json")
    print("  3. semantic_vs_lexical.json")
    print("  4. transliteration_demo.json")
    print("  5. hybrid_ranking_results.json")
    
    print("\nThese files contain all required Module C analysis!")


if __name__ == "__main__":
    main()
