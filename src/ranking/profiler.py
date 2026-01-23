"""
Query Profiler
Tracks query execution time with breakdown by pipeline stage
"""

import time
from contextlib import contextmanager


class QueryProfiler:
    """
    Track query execution time with detailed breakdown
    """

    def __init__(self):
        """Initialize the profiler"""
        self.timings = {}
        self.current_query = None
        self.current_start = None

    @contextmanager
    def track_query(self, query):
        """
        Context manager for tracking full query execution

        Usage:
            with profiler.track_query('my query'):
                # do query processing
                with profiler.track_stage('translation'):
                    translate()
                with profiler.track_stage('retrieval'):
                    retrieve()

        Args:
            query (str): Query text

        Yields:
            QueryProfiler: self for chaining
        """
        self.current_query = query
        self.timings[query] = {
            'total_time_ms': 0,
            'stages': {},
            'start_time': time.time()
        }

        start = time.perf_counter()
        try:
            yield self
        finally:
            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            self.timings[query]['total_time_ms'] = elapsed
            self.timings[query]['end_time'] = time.time()
            self.current_query = None

    @contextmanager
    def track_stage(self, stage_name):
        """
        Context manager for tracking individual pipeline stage

        Args:
            stage_name (str): Name of the stage (e.g., 'translation', 'retrieval')

        Yields:
            None
        """
        if self.current_query is None:
            # Not in a query context, just run without tracking
            yield
            return

        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            self.timings[self.current_query]['stages'][stage_name] = elapsed

    def get_report(self, query):
        """
        Get timing report for a query

        Args:
            query (str): Query text

        Returns:
            dict: Timing report
                {
                    'query': str,
                    'total_time_ms': 245.3,
                    'stages': {
                        'translation': 12.5,
                        'embedding': 180.2,
                        'ranking': 52.6
                    },
                    'breakdown_percentage': {
                        'translation': 5.1,
                        'embedding': 73.5,
                        'ranking': 21.4
                    }
                }
        """
        if query not in self.timings:
            return {
                'query': query,
                'total_time_ms': 0,
                'stages': {},
                'breakdown_percentage': {}
            }

        timing = self.timings[query]
        total = timing['total_time_ms']

        # Calculate percentages
        breakdown_percentage = {}
        if total > 0:
            for stage, time_ms in timing['stages'].items():
                breakdown_percentage[stage] = (time_ms / total) * 100

        return {
            'query': query,
            'total_time_ms': total,
            'stages': timing['stages'],
            'breakdown_percentage': breakdown_percentage
        }

    def get_all_reports(self):
        """
        Get timing reports for all queries

        Returns:
            list: List of timing reports
        """
        return [self.get_report(query) for query in self.timings.keys()]

    def print_report(self, query):
        """
        Print formatted timing report for a query

        Args:
            query (str): Query text
        """
        report = self.get_report(query)

        print(f"\n{'='*70}")
        print(f"Query Execution Time Report")
        print(f"{'='*70}")
        print(f"Query: '{report['query']}'")
        print(f"Total Time: {report['total_time_ms']:.2f} ms")
        print(f"\nBreakdown by Stage:")
        print(f"{'-'*70}")

        for stage, time_ms in report['stages'].items():
            percentage = report['breakdown_percentage'].get(stage, 0)
            print(f"  {stage:20s}: {time_ms:8.2f} ms ({percentage:5.1f}%)")

        print(f"{'='*70}\n")

    def print_summary(self):
        """
        Print summary of all queries

        Useful for comparing performance across multiple queries
        """
        if not self.timings:
            print("No queries profiled yet.")
            return

        print(f"\n{'='*70}")
        print(f"Query Performance Summary")
        print(f"{'='*70}")
        print(f"Total Queries: {len(self.timings)}")
        print(f"\nQuery Times:")
        print(f"{'-'*70}")

        for query, timing in self.timings.items():
            total = timing['total_time_ms']
            query_short = query[:40] + '...' if len(query) > 40 else query
            print(f"  {query_short:45s}: {total:8.2f} ms")

        # Calculate average
        total_times = [t['total_time_ms'] for t in self.timings.values()]
        avg_time = sum(total_times) / len(total_times) if total_times else 0

        print(f"{'-'*70}")
        print(f"  {'Average':45s}: {avg_time:8.2f} ms")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    # Test the profiler
    print("Testing QueryProfiler...")

    profiler = QueryProfiler()

    # Simulate query processing
    with profiler.track_query('bangladesh cricket team'):
        # Simulate translation
        with profiler.track_stage('translation'):
            time.sleep(0.01)  # 10ms

        # Simulate BM25 retrieval
        with profiler.track_stage('bm25_retrieval'):
            time.sleep(0.005)  # 5ms

        # Simulate semantic retrieval
        with profiler.track_stage('semantic_retrieval'):
            time.sleep(0.02)  # 20ms

        # Simulate ranking
        with profiler.track_stage('ranking'):
            time.sleep(0.003)  # 3ms

    # Print report
    profiler.print_report('bangladesh cricket team')

    # Simulate another query
    with profiler.track_query('education system'):
        with profiler.track_stage('translation'):
            time.sleep(0.012)
        with profiler.track_stage('semantic_retrieval'):
            time.sleep(0.025)

    # Print summary
    profiler.print_summary()

    print(" QueryProfiler test passed!")
