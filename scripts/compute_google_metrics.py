"""
Compute metrics for Google Search results by cross-referencing with labeled queries.
Since Google returns different URLs than our corpus, we assess relevance based on:
1. Direct URL overlap with our labeled relevant documents
2. Domain-level relevance matching
"""

import pandas as pd
import numpy as np
from urllib.parse import urlparse
import json

def normalize_url(url):
    """Normalize URL for comparison."""
    if pd.isna(url):
        return ""
    url = url.lower().strip()
    # Remove protocol
    url = url.replace("https://", "").replace("http://", "")
    # Remove www prefix
    url = url.replace("www.", "")
    # Remove trailing slash
    url = url.rstrip("/")
    return url

def get_domain(url):
    """Extract domain from URL."""
    if pd.isna(url):
        return ""
    try:
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        return parsed.netloc.replace("www.", "")
    except:
        return ""

def compute_precision_at_k(relevance_list, k=10):
    """Compute Precision@k."""
    relevance_list = relevance_list[:k]
    if len(relevance_list) == 0:
        return 0.0
    return sum(relevance_list) / len(relevance_list)

def compute_mrr(relevance_list):
    """Compute Mean Reciprocal Rank."""
    for i, rel in enumerate(relevance_list):
        if rel:
            return 1.0 / (i + 1)
    return 0.0

def compute_dcg(relevance_list, k=10):
    """Compute DCG@k."""
    relevance_list = relevance_list[:k]
    dcg = 0.0
    for i, rel in enumerate(relevance_list):
        dcg += rel / np.log2(i + 2)  # i+2 because log2(1) = 0
    return dcg

def compute_ndcg(relevance_list, k=10):
    """Compute nDCG@k."""
    dcg = compute_dcg(relevance_list, k)
    # Ideal DCG: all relevant at top
    ideal_relevance = sorted(relevance_list, reverse=True)
    idcg = compute_dcg(ideal_relevance, k)
    if idcg == 0:
        return 0.0
    return dcg / idcg

def main():
    # Load data
    google_results = pd.read_csv("data/evaluation/search_engine_results.csv", encoding='utf-8')
    labeled_queries = pd.read_csv("data/evaluation/labeled_queries.csv", encoding='utf-8')

    # Get unique queries from Google results
    queries = google_results['query'].unique()
    print(f"Found {len(queries)} queries in Google results")

    # Build set of relevant domains per query from labeled data
    query_relevant_domains = {}
    query_relevant_urls = {}

    for query in queries:
        query_labels = labeled_queries[labeled_queries['query'] == query]
        relevant_docs = query_labels[query_labels['relevant'] == 'yes']

        # Store relevant domains
        relevant_domains = set()
        relevant_urls = set()
        for url in relevant_docs['doc_url']:
            domain = get_domain(url)
            if domain:
                relevant_domains.add(domain)
            relevant_urls.add(normalize_url(url))

        query_relevant_domains[query] = relevant_domains
        query_relevant_urls[query] = relevant_urls

    # Common relevant domains across queries (news sources we know are relevant)
    # Based on the labeled data, these domains frequently contain relevant content
    relevant_news_domains = {
        'prothomalo.com', 'thedailystar.net', 'dhakatribune.com',
        'aljazeera.com', 'bbc.com', 'newagebd.net', 'dailynewnation.com',
        'espncricinfo.com', 'cricbuzz.com'
    }

    # Compute metrics for each query
    all_precisions = []
    all_mrrs = []
    all_ndcgs = []

    query_details = []

    for query in queries:
        query_google = google_results[google_results['query'] == query].sort_values('rank')

        # Assess relevance for each Google result
        relevance_list = []
        for _, row in query_google.iterrows():
            url = row['url']
            normalized = normalize_url(url)
            domain = get_domain(url)

            # Check relevance:
            # 1. Direct URL match (unlikely since different sources)
            # 2. Domain is in our known relevant news sources for this query type
            is_relevant = False

            # Check if domain matches any relevant domains for this query
            if domain in query_relevant_domains.get(query, set()):
                is_relevant = True
            # Or if it's a known relevant news domain
            elif domain in relevant_news_domains:
                is_relevant = True
            # Wikipedia and government sources are generally relevant for informational queries
            elif 'wikipedia.org' in domain or '.gov.bd' in domain:
                is_relevant = True
            # Social media and translation proxies are less likely to be high-quality
            elif 'facebook.com' in domain or 'translate.goog' in domain:
                is_relevant = False

            relevance_list.append(1 if is_relevant else 0)

        # Pad to 10 if needed
        while len(relevance_list) < 10:
            relevance_list.append(0)

        p_at_10 = compute_precision_at_k(relevance_list, 10)
        mrr = compute_mrr(relevance_list)
        ndcg = compute_ndcg(relevance_list, 10)

        all_precisions.append(p_at_10)
        all_mrrs.append(mrr)
        all_ndcgs.append(ndcg)

        query_details.append({
            'query': query,
            'num_results': len(query_google),
            'relevance': relevance_list[:len(query_google)],
            'p@10': p_at_10,
            'mrr': mrr,
            'ndcg@10': ndcg
        })

    # Compute averages
    avg_precision = np.mean(all_precisions)
    avg_mrr = np.mean(all_mrrs)
    avg_ndcg = np.mean(all_ndcgs)

    print("\n" + "="*60)
    print("GOOGLE SEARCH METRICS (Estimated based on domain relevance)")
    print("="*60)
    print(f"Precision@10: {avg_precision:.2f}")
    print(f"MRR: {avg_mrr:.2f}")
    print(f"nDCG@10: {avg_ndcg:.2f}")
    print(f"Number of queries: {len(queries)}")

    print("\n" + "="*60)
    print("PER-QUERY DETAILS")
    print("="*60)
    for detail in query_details:
        # Truncate query for display, handle unicode safely
        query_short = detail['query'][:50] if len(detail['query']) > 50 else detail['query']
        try:
            print(f"\nQuery: {query_short}...")
        except UnicodeEncodeError:
            print(f"\nQuery: [Bengali/Mixed query]...")
        print(f"  Results: {detail['num_results']}, Relevance: {detail['relevance']}")
        print(f"  P@10: {detail['p@10']:.2f}, MRR: {detail['mrr']:.2f}, nDCG@10: {detail['ndcg@10']:.2f}")

    # Save results
    results = {
        'google_metrics': {
            'precision@10': round(avg_precision, 2),
            'mrr': round(avg_mrr, 2),
            'ndcg@10': round(avg_ndcg, 2),
            'num_queries': len(queries)
        },
        'per_query': query_details,
        'methodology': 'Relevance estimated based on domain matching with labeled corpus and known relevant news domains'
    }

    with open('data/evaluation/results/module_d_results/google_metrics.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\nResults saved to data/evaluation/results/module_d_results/google_metrics.json")

    return results

if __name__ == "__main__":
    main()
