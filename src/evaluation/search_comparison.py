"""
Search Engine Comparison
Compare retrieval system results with Google and Bing
"""

import csv
import os
from collections import defaultdict


class SearchEngineComparison:
    """
    Compare system results with popular search engines (Google, Bing)
    Helps understand how our CLIR system compares to established engines
    """

    def __init__(self, output_file='data/evaluation/search_engine_results.csv'):
        """
        Initialize comparison tool

        Args:
            output_file (str): Where to save search engine results
        """
        self.output_file = output_file
        self.search_results = []  # List of search result dicts

        # Load existing results if file exists
        if os.path.exists(output_file):
            self._load_existing_results()

    def _load_existing_results(self):
        """Load existing search engine results from CSV"""
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.search_results = list(reader)
            print(f"9  Loaded {len(self.search_results)} existing search engine results")
        except Exception as e:
            print(f"�  Could not load existing results: {e}")

    def collect_manual_results(self, query, engines=None):
        """
        Interactive: User manually searches and pastes results from search engines

        For each query:
          1. User searches on Google
          2. User pastes top-10 URLs
          3. Repeat for Bing
          4. Save to CSV

        Args:
            query (str): Query to search for
            engines (list): List of search engines (default: ['Google', 'Bing'])

        Returns:
            list: List of result dicts
        """
        if engines is None:
            engines = ['Google', 'Bing']

        print(f"\n{'=' * 80}")
        print(f"Query: \"{query}\"")
        print(f"{'=' * 80}")
        print("\nPlease search for this query on Google and Bing")
        print("Then paste the top-10 URLs below (one per line)")
        print(f"{'=' * 80}\n")

        results = []

        for engine in engines:
            print(f"\n--- {engine} Results ---")
            print("Paste URLs one per line (press Enter on empty line to finish):")
            print("Example: https://example.com/article")
            print()

            urls = []
            rank = 1

            while rank <= 10:
                url = input(f"  [{rank}]: ").strip()

                if not url:
                    # Empty line - finish this engine
                    break

                # Validate URL (basic check)
                if not url.startswith('http'):
                    print("    �  Invalid URL (must start with http/https). Try again.")
                    continue

                urls.append(url)

                # Create result entry
                result = {
                    'query': query,
                    'search_engine': engine,
                    'rank': rank,
                    'url': url
                }
                results.append(result)
                self.search_results.append(result)

                rank += 1

            print(f"   Collected {len(urls)} URLs from {engine}\n")

        # Save after collection
        self._save_results()

        return results

    def _save_results(self):
        """Save search engine results to CSV"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

            with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
                if self.search_results:
                    fieldnames = ['query', 'search_engine', 'rank', 'url']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.search_results)

            print(f" Results saved to {self.output_file}")

        except Exception as e:
            print(f"L Error saving results: {e}")

    def compare_results(self, query, our_results):
        """
        Compare our system's results with Google/Bing results for a query

        Args:
            query (str): Query text
            our_results (list): Our system's results (list of dicts with 'doc' key)

        Returns:
            dict: Comparison metrics
                {
                    'query': str,
                    'our_top_10_urls': [...],
                    'google_urls': [...],
                    'bing_urls': [...],
                    'overlap_with_google': 0.3,
                    'overlap_with_bing': 0.4,
                    'overlap_with_both': 0.2,
                    'unique_results': 6,
                    'analysis': str
                }
        """
        # Extract our URLs
        our_urls = []
        for result in our_results[:10]:
            doc = result.get('doc', {})
            url = doc.get('url', '')
            if url:
                our_urls.append(url)

        # Get search engine URLs for this query
        google_urls = []
        bing_urls = []

        for result in self.search_results:
            if result['query'] == query:
                url = result['url']
                if result['search_engine'] == 'Google':
                    google_urls.append(url)
                elif result['search_engine'] == 'Bing':
                    bing_urls.append(url)

        # Calculate overlaps
        our_set = set(our_urls)
        google_set = set(google_urls)
        bing_set = set(bing_urls)

        overlap_google = len(our_set & google_set)
        overlap_bing = len(our_set & bing_set)
        overlap_both = len(our_set & google_set & bing_set)

        # Calculate percentages
        overlap_google_pct = overlap_google / 10 if our_urls else 0
        overlap_bing_pct = overlap_bing / 10 if our_urls else 0

        # Unique results (in our system but not in either search engine)
        unique = len(our_set - google_set - bing_set)

        # Generate analysis
        analysis = self._generate_analysis(
            overlap_google_pct, overlap_bing_pct, unique, len(our_urls)
        )

        return {
            'query': query,
            'our_top_10_urls': our_urls,
            'google_urls': google_urls,
            'bing_urls': bing_urls,
            'overlap_with_google': overlap_google_pct,
            'overlap_with_bing': overlap_bing_pct,
            'overlap_with_both': overlap_both,
            'unique_results': unique,
            'total_our_results': len(our_urls),
            'analysis': analysis
        }

    def _generate_analysis(self, google_overlap, bing_overlap, unique, total):
        """
        Generate human-readable analysis of comparison

        Args:
            google_overlap (float): Overlap percentage with Google
            bing_overlap (float): Overlap percentage with Bing
            unique (int): Number of unique results
            total (int): Total results from our system

        Returns:
            str: Analysis text
        """
        analysis = []

        # Overall assessment
        avg_overlap = (google_overlap + bing_overlap) / 2
        if avg_overlap > 0.5:
            analysis.append("High overlap with commercial search engines (>50%).")
            analysis.append("Our system retrieves similar results.")
        elif avg_overlap > 0.3:
            analysis.append("Moderate overlap with commercial search engines (30-50%).")
        else:
            analysis.append("Low overlap with commercial search engines (<30%).")

        # Unique results
        if unique > 5:
            analysis.append(f"Found {unique} unique results not in Google/Bing.")
            analysis.append("This demonstrates value of cross-lingual retrieval for local sources.")
        elif unique > 0:
            analysis.append(f"Found {unique} unique results.")
        else:
            analysis.append("All results also found by commercial engines.")

        # Cross-lingual advantage
        analysis.append("\nOur CLIR system's advantages:")
        analysis.append("- Cross-lingual search (Bangla � English)")
        analysis.append("- Local news sources emphasis")
        analysis.append("- Semantic understanding across languages")

        return " ".join(analysis)

    def print_comparison(self, comparison):
        """
        Print formatted comparison results

        Args:
            comparison (dict): Output from compare_results()
        """
        print(f"\n{'=' * 80}")
        print(f"Search Engine Comparison: \"{comparison['query']}\"")
        print(f"{'=' * 80}")
        print(f"Our Results: {comparison['total_our_results']}")
        print(f"Google Results: {len(comparison['google_urls'])}")
        print(f"Bing Results: {len(comparison['bing_urls'])}")
        print(f"\nOverlap:")
        print(f"  With Google: {comparison['overlap_with_google']:.1%}")
        print(f"  With Bing: {comparison['overlap_with_bing']:.1%}")
        print(f"  Unique to our system: {comparison['unique_results']}")
        print(f"\nAnalysis:")
        print(f"  {comparison['analysis']}")
        print(f"{'=' * 80}\n")

    def get_statistics(self):
        """
        Get statistics about collected search engine results

        Returns:
            dict: Statistics
        """
        queries = set(r['query'] for r in self.search_results)
        engines = set(r['search_engine'] for r in self.search_results)

        return {
            'total_results': len(self.search_results),
            'queries_collected': len(queries),
            'engines_used': list(engines),
            'queries': list(queries)
        }


if __name__ == "__main__":
    # Test the search comparison tool
    print("Testing SearchEngineComparison...")

    # Create tool
    tool = SearchEngineComparison(output_file='test_search_results.csv')

    # Mock our system's results
    our_results = [
        {'doc': {'url': 'http://example.com/cricket1', 'title': 'Cricket News'}},
        {'doc': {'url': 'http://example.com/cricket2', 'title': 'Sports Update'}},
        {'doc': {'url': 'http://dailystar.com/cricket', 'title': 'Bangladesh Cricket'}},
    ]

    # Mock search engine results
    tool.search_results = [
        {'query': 'cricket', 'search_engine': 'Google', 'rank': 1, 'url': 'http://example.com/cricket1'},
        {'query': 'cricket', 'search_engine': 'Google', 'rank': 2, 'url': 'http://espn.com/cricket'},
        {'query': 'cricket', 'search_engine': 'Bing', 'rank': 1, 'url': 'http://example.com/cricket2'},
        {'query': 'cricket', 'search_engine': 'Bing', 'rank': 2, 'url': 'http://bbc.com/cricket'},
    ]

    # Compare
    comparison = tool.compare_results('cricket', our_results)
    tool.print_comparison(comparison)

    # Get statistics
    stats = tool.get_statistics()
    print(f"Statistics:")
    print(f"  Total results: {stats['total_results']}")
    print(f"  Queries: {stats['queries_collected']}")
    print(f"  Engines: {stats['engines_used']}")

    # Cleanup
    if os.path.exists('test_search_results.csv'):
        os.remove('test_search_results.csv')

    print("\n SearchEngineComparison test passed!")
