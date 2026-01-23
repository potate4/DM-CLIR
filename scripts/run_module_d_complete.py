"""
Module D - Complete Pipeline
Runs the entire Module D workflow from ranking to evaluation
"""

import sys
import os
import subprocess

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def run_script(script_name, description):
    """
    Run a Python script

    Args:
        script_name (str): Name of script to run
        description (str): Description of what the script does

    Returns:
        int: Return code from script
    """
    print("\n" + "=" * 80)
    print(f"STEP: {description}")
    print("=" * 80)

    script_path = os.path.join(os.path.dirname(__file__), script_name)

    if not os.path.exists(script_path):
        print(f"L Script not found: {script_path}")
        return 1

    # Run the script
    result = subprocess.run([sys.executable, script_path])

    return result.returncode


def main():
    """Main execution - orchestrates entire Module D pipeline"""
    print("=" * 80)
    print("MODULE D - COMPLETE PIPELINE")
    print("Ranking, Scoring, & Evaluation")
    print("=" * 80)

    print("\nThis script will guide you through the complete Module D workflow:")
    print("  1. Ranking Demo - Show normalized scores and confidence warnings")
    print("  2. Relevance Labeling - Create relevance judgments (interactive)")
    print("  3. Evaluation - Calculate IR metrics")
    print("  4. Search Comparison - Compare with Google/Bing (optional)")
    print("  5. Error Analysis - Analyze 5 error categories")

    input("\nPress Enter to start...")

    # Step 1: Ranking Demo
    print("\n\n" + "#" * 80)
    print("STEP 1 of 5: RANKING DEMO")
    print("#" * 80)
    print("This will demonstrate:")
    print("  - Score normalization to [0, 1]")
    print("  - Confidence warnings for low-quality results")
    print("  - Execution time tracking")

    response = input("\nRun ranking demo? (y/n): ").strip().lower()
    if response == 'y':
        ret_code = run_script('run_module_d_ranking.py', 'Ranking Demo')
        if ret_code != 0:
            print("�  Ranking demo encountered an error")
    else:
        print("Skipping ranking demo...")

    # Step 2: Relevance Labeling
    print("\n\n" + "#" * 80)
    print("STEP 2 of 5: RELEVANCE LABELING")
    print("#" * 80)
    print("This will:")
    print("  - Let you label query results as relevant or not relevant")
    print("  - Create a CSV file with relevance labels")
    print("  - Take approximately 15-20 minutes for 5-10 queries")

    response = input("\nRun labeling tool? (y/n): ").strip().lower()
    if response == 'y':
        ret_code = run_script('run_module_d_labeling.py', 'Relevance Labeling')
        if ret_code != 0:
            print("   Labeling encountered an error or was interrupted")
            print("You can resume labeling later by running:")
            print("  python scripts/run_module_d_labeling.py")
    else:
        print("Skipping labeling...")
        print("Note: You'll need labels to run evaluation!")

    # Step 3: Evaluation
    print("\n\n" + "#" * 80)
    print("STEP 3 of 5: EVALUATION")
    print("#" * 80)
    print("This will:")
    print("  - Calculate Precision@10, Recall@50, nDCG@10, MRR")
    print("  - Compare all retrieval models")
    print("  - Check if models meet target thresholds")

    # Check if labels exist
    labels_file = 'data/evaluation/labeled_queries.csv'
    if not os.path.exists(labels_file):
        print(f"\n   Labels file not found: {labels_file}")
        print("Skipping evaluation (labels required)")
    else:
        response = input("\nRun evaluation? (y/n): ").strip().lower()
        if response == 'y':
            ret_code = run_script('run_module_d_evaluation.py', 'Evaluation')
            if ret_code != 0:
                print("   Evaluation encountered an error")
        else:
            print("Skipping evaluation...")

    # Step 4: Search Engine Comparison (Optional)
    print("\n\n" + "#" * 80)
    print("STEP 4 of 5: SEARCH ENGINE COMPARISON (Optional)")
    print("#" * 80)
    print("This will:")
    print("  - Compare results with Google and Bing")
    print("  - Require manual searching and pasting URLs")
    print("  - Take approximately 10-15 minutes for 3-5 queries")

    response = input("\nRun search engine comparison? (y/n): ").strip().lower()
    if response == 'y':
        ret_code = run_script('run_module_d_comparison.py', 'Search Engine Comparison')
        if ret_code != 0:
            print("   Comparison encountered an error")
    else:
        print("Skipping search engine comparison...")

    # Step 5: Error Analysis
    print("\n\n" + "#" * 80)
    print("STEP 5 of 5: ERROR ANALYSIS")
    print("#" * 80)
    print("This will analyze 5 error categories:")
    print("  1. Translation Failures")
    print("  2. Named Entity Mismatch")
    print("  3. Semantic vs Lexical Wins")
    print("  4. Cross-Script Ambiguity")
    print("  5. Code-Switching")

    response = input("\nRun error analysis? (y/n): ").strip().lower()
    if response == 'y':
        ret_code = run_script('run_module_d_error_analysis.py', 'Error Analysis')
        if ret_code != 0:
            print("   Error analysis encountered an error")
    else:
        print("Skipping error analysis...")

    # Final summary
    print("\n\n" + "=" * 80)
    print("MODULE D COMPLETE!")
    print("=" * 80)

    print("\nGenerated files:")
    print("  =� Rankings:")
    print("     data/evaluation/results/module_d_results/ranking_results.json")

    if os.path.exists('data/evaluation/labeled_queries.csv'):
        print("  =� Labels:")
        print("     data/evaluation/labeled_queries.csv")

    if os.path.exists('data/evaluation/results/module_d_results/evaluation_metrics.json'):
        print("  =� Metrics:")
        print("     data/evaluation/results/module_d_results/evaluation_metrics.json")
        print("     data/evaluation/results/module_d_results/metrics_comparison.csv")

    if os.path.exists('data/evaluation/results/module_d_results/search_comparison.json'):
        print("  =Comparison:")
        print("     data/evaluation/results/module_d_results/search_comparison.json")

    if os.path.exists('data/evaluation/results/module_d_results/error_analysis.json'):
        print("  = Error Analysis:")
        print("     data/evaluation/results/module_d_results/error_analysis.json")

    print("\n" + "=" * 80)
    print("Next steps:")
    print("  - Review all generated files")
    print("  - Use results for your report")
    print("  - Create visualizations (optional)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
