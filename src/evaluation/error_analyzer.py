"""
Error Analyzer
Analyzes 5 required error categories for Module D
"""

import json
from collections import defaultdict


class ErrorAnalyzer:
    """
    Analyze retrieval failures across 5 required categories:
    1. Translation Failures
    2. Named Entity Mismatch
    3. Semantic vs Lexical Wins
    4. Cross-Script Ambiguity
    5. Code-Switching
    """

    def __init__(self):
        """Initialize error analyzer"""
        self.categories = {
            'translation_failures': [],
            'named_entity_mismatch': [],
            'semantic_vs_lexical': [],
            'cross_script_ambiguity': [],
            'code_switching': []
        }

    def _get_score(self, result, prefer_raw=True):
        """
        Get score from result, preferring raw_score for analysis when available.

        Args:
            result (dict): Result dictionary with 'score' and optionally 'raw_score'
            prefer_raw (bool): If True, prefer raw_score over normalized score

        Returns:
            float: The score value
        """
        if prefer_raw and 'raw_score' in result:
            return result['raw_score']
        return result.get('score', 0)

    def analyze_translation_failures(self, query, translation_data, retrieval_results):
        """
        Category 1: Translation Failures

        Example: "চেয়ার" (chair) → "Chairman" (incorrect translation)
        Results in retrieving irrelevant documents

        Args:
            query (str): Original query
            translation_data (dict): Translation information
                {
                    'original': 'চেয়ার',
                    'translated': 'Chairman',
                    'method': 'google_translate',
                    'expected': 'chair' (optional)
                }
            retrieval_results (dict): Results from all models

        Returns:
            dict: Analysis of translation failure
        """
        original = translation_data.get('original', query)
        translated = translation_data.get('translated', '')
        method = translation_data.get('method', 'unknown')

        # Check if BM25 failed due to bad translation (use raw score for analysis)
        bm25_top_score = 0
        bm25_raw_score = 0
        if 'BM25' in retrieval_results and retrieval_results['BM25']:
            bm25_top_score = retrieval_results['BM25'][0].get('score', 0)
            bm25_raw_score = self._get_score(retrieval_results['BM25'][0], prefer_raw=True)

        # Check if Semantic succeeded despite translation
        semantic_top_score = 0
        if 'Semantic' in retrieval_results and retrieval_results['Semantic']:
            semantic_top_score = retrieval_results['Semantic'][0].get('score', 0)

        case = {
            'category': 'translation_failure',
            'query_original': original,
            'query_translated': translated,
            'translation_method': method,
            'expected_translation': translation_data.get('expected', 'N/A'),
            'bm25_top_score': bm25_top_score,
            'bm25_raw_score': bm25_raw_score,
            'semantic_top_score': semantic_top_score,
            'impact': self._assess_translation_impact(bm25_raw_score, semantic_top_score),
            'recommendation': 'Use dictionary for common words or verify translation quality'
        }

        self.categories['translation_failures'].append(case)
        return case

    def analyze_entity_mismatch(self, query, entities, retrieval_results):
        """
        Category 2: Named Entity Mismatch

        Example: Query has "ঢাকা" (Dhaka in Bangla), documents have "Dhaka" (English)
        Lexical models fail to match, semantic models succeed

        Args:
            query (str): Query text
            entities (list): List of detected entities
                [{'text': 'ঢাকা', 'type': 'GPE', 'variants': ['Dhaka', 'Dacca']}, ...]
            retrieval_results (dict): Results from all models

        Returns:
            dict: Analysis of entity mismatch
        """
        if not entities:
            return None

        # Get normalized scores for display, raw scores for analysis
        model_scores = {}
        raw_scores = {}
        for model_name in ['BM25', 'Fuzzy', 'Semantic']:
            if model_name in retrieval_results and retrieval_results[model_name]:
                model_scores[model_name] = retrieval_results[model_name][0].get('score', 0)
                raw_scores[model_name] = self._get_score(retrieval_results[model_name][0], prefer_raw=True)

        case = {
            'category': 'named_entity_mismatch',
            'query': query,
            'entities': entities,
            'model_scores': model_scores,
            'raw_scores': raw_scores,
            'bm25_score': model_scores.get('BM25', 0),
            'fuzzy_score': model_scores.get('Fuzzy', 0),
            'semantic_score': model_scores.get('Semantic', 0),
            'analysis': self._assess_entity_matching(model_scores, raw_scores),
            'recommendation': 'Add NER mapping layer to handle cross-lingual entity matching'
        }

        self.categories['named_entity_mismatch'].append(case)
        return case

    def analyze_semantic_lexical_wins(self, query, all_results):
        """
        Category 3: Semantic vs Lexical Wins

        Example: Query "শিক্ষা" (education), BM25=0 (no match), Semantic retrieves "স্কুল" (school)

        Args:
            query (str): Query text
            all_results (dict): Results from all models
                {
                    'BM25': [...],
                    'Semantic': [...]
                }

        Returns:
            dict: Analysis of semantic vs lexical performance
        """
        # Get normalized scores for display
        lexical_score = 0  # Max of BM25, TF-IDF (normalized)
        semantic_score = 0

        # Get raw scores for analysis
        bm25_raw = 0

        if 'BM25' in all_results and all_results['BM25']:
            lexical_score = max(lexical_score, all_results['BM25'][0].get('score', 0))
            bm25_raw = self._get_score(all_results['BM25'][0], prefer_raw=True)

        if 'TF-IDF' in all_results and all_results['TF-IDF']:
            lexical_score = max(lexical_score, all_results['TF-IDF'][0].get('score', 0))

        if 'Semantic' in all_results and all_results['Semantic']:
            semantic_score = all_results['Semantic'][0].get('score', 0)

        # Determine winner using raw BM25 score for better analysis
        # Raw BM25: < 5 is weak, 5-15 is moderate, > 15 is strong
        # Semantic: cosine similarity 0-1
        if bm25_raw < 5.0 and semantic_score > 0.6:
            winner = 'semantic'
            reason = 'Cross-lingual semantic matching; lexical models failed due to script/language mismatch'
        elif bm25_raw > 15.0 and semantic_score < 0.5:
            winner = 'lexical'
            reason = 'Exact term matching; query and documents share common terms'
        elif bm25_raw > 10.0 and semantic_score > 0.7:
            winner = 'both'
            reason = 'Both approaches found relevant documents'
        else:
            winner = 'tie'
            reason = 'Both approaches perform similarly'

        case = {
            'category': 'semantic_vs_lexical',
            'query': query,
            'semantic_wins': winner == 'semantic',
            'lexical_wins': winner == 'lexical',
            'winner': winner,
            'reason': reason,
            'lexical_top_score': lexical_score,
            'lexical_raw_score': bm25_raw,
            'semantic_top_score': semantic_score,
            'score_difference': semantic_score - lexical_score,
            'case_study': self._generate_semantic_lexical_case_study(query, winner, all_results)
        }

        self.categories['semantic_vs_lexical'].append(case)
        return case

    def analyze_cross_script_ambiguity(self, query_variants, retrieval_results_per_variant):
        """
        Category 4: Cross-Script Ambiguity

        Example: "Bangladesh" vs "বাংলাদেশ" vs "Bangla Desh" (two words)
        Which transliterations work with which models?

        Args:
            query_variants (list): List of query variants
                ['Bangladesh', 'বাংলাদেশ', 'Bangla Desh']
            retrieval_results_per_variant (dict): Results for each variant
                {
                    'Bangladesh': {'BM25': [...], 'Semantic': [...]},
                    'বাংলাদেশ': {...},
                    'Bangla Desh': {...}
                }

        Returns:
            dict: Analysis of cross-script handling
        """
        # Aggregate normalized and raw scores for each variant across models
        variant_scores = {}
        variant_raw_scores = {}

        for variant in query_variants:
            if variant not in retrieval_results_per_variant:
                continue

            results = retrieval_results_per_variant[variant]
            variant_scores[variant] = {}
            variant_raw_scores[variant] = {}

            for model_name in ['BM25', 'Fuzzy', 'Semantic']:
                if model_name in results and results[model_name]:
                    variant_scores[variant][model_name] = results[model_name][0].get('score', 0)
                    variant_raw_scores[variant][model_name] = self._get_score(
                        results[model_name][0], prefer_raw=True
                    )

        # Find best variant for each model (using raw scores for BM25/Fuzzy)
        best_variants = {}
        for model_name in ['BM25', 'Fuzzy', 'Semantic']:
            best_score = 0
            best_variant = None

            for variant in variant_scores:
                # Use raw score for BM25/Fuzzy, normalized for Semantic
                if model_name in ['BM25', 'Fuzzy']:
                    score = variant_raw_scores.get(variant, {}).get(model_name, 0)
                else:
                    score = variant_scores.get(variant, {}).get(model_name, 0)

                if score > best_score:
                    best_score = score
                    best_variant = variant

            best_variants[model_name] = best_variant

        case = {
            'category': 'cross_script_ambiguity',
            'query_variants': query_variants,
            'variant_scores': variant_scores,
            'variant_raw_scores': variant_raw_scores,
            'best_variant_per_model': best_variants,
            'analysis': self._assess_cross_script_handling(variant_scores, best_variants),
            'recommendation': 'Add transliteration preprocessing to normalize variants'
        }

        self.categories['cross_script_ambiguity'].append(case)
        return case

    def analyze_code_switching(self, query, language_mix, retrieval_results):
        """
        Category 5: Code-Switching

        Example: "Bangladesh এর cricket টিম" (mixes English and Bangla)
        Does the system handle mixed-language queries?

        Args:
            query (str): Mixed-language query
            language_mix (dict): Language detection info
                {
                    'detected_languages': ['english', 'bangla'],
                    'primary_language': 'bangla',
                    'code_switching_detected': True
                }
            retrieval_results (dict): Results from all models

        Returns:
            dict: Analysis of code-switching handling
        """
        # Get normalized scores for display, raw scores for analysis
        model_scores = {}
        raw_scores = {}
        for model_name in ['BM25', 'TF-IDF', 'Fuzzy', 'Semantic']:
            if model_name in retrieval_results and retrieval_results[model_name]:
                model_scores[model_name] = retrieval_results[model_name][0].get('score', 0)
                raw_scores[model_name] = self._get_score(retrieval_results[model_name][0], prefer_raw=True)

        # Use raw BM25 score for analysis
        bm25_score = model_scores.get('BM25', 0)
        bm25_raw = raw_scores.get('BM25', 0)
        semantic_score = model_scores.get('Semantic', 0)

        # Assess handling quality using raw scores
        # Raw BM25: < 5 is weak, 5-15 is moderate, > 15 is strong
        if semantic_score > 0.6 and bm25_raw < 5.0:
            handling = 'good'
            analysis = 'Semantic model handles code-switching better than lexical'
        elif bm25_raw >= 5.0:
            handling = 'partial'
            analysis = 'BM25 partially matches on shared terms'
        else:
            handling = 'poor'
            analysis = 'Both models struggle with mixed-language query'

        case = {
            'category': 'code_switching',
            'query': query,
            'languages_detected': language_mix.get('detected_languages', []),
            'code_switching': language_mix.get('code_switching_detected', False),
            'model_scores': model_scores,
            'raw_scores': raw_scores,
            'bm25_score': bm25_score,
            'bm25_raw_score': bm25_raw,
            'semantic_score': semantic_score,
            'handling_quality': handling,
            'analysis': analysis,
            'recommendation': 'Language-agnostic embeddings (like LaBSE) help with code-switching'
        }

        self.categories['code_switching'].append(case)
        return case

    def _assess_translation_impact(self, bm25_raw_score, semantic_score):
        """
        Assess impact of translation quality.

        Args:
            bm25_raw_score: Raw BM25 score (typically 0-30+ range)
            semantic_score: Semantic similarity score (0-1 range)
        """
        # Raw BM25 scores: < 2 is very weak match, < 5 is weak, > 10 is strong
        if bm25_raw_score < 2.0 and semantic_score > 0.5:
            return "High impact: Bad translation caused BM25 failure, but Semantic succeeded"
        elif bm25_raw_score < 2.0:
            return "Critical impact: Bad translation caused complete retrieval failure"
        elif bm25_raw_score < 5.0:
            return "Medium impact: Translation partially affected BM25 retrieval quality"
        else:
            return "Low impact: Translation quality did not significantly affect retrieval"

    def _assess_entity_matching(self, model_scores, raw_scores=None):
        """
        Assess entity matching across models.

        Args:
            model_scores: Normalized scores (0-1)
            raw_scores: Raw scores from retrievers (optional, for better analysis)
        """
        semantic = model_scores.get('Semantic', 0)
        fuzzy = model_scores.get('Fuzzy', 0)

        # Use raw BM25 score if available (typically 0-30+ range)
        if raw_scores and 'BM25' in raw_scores:
            bm25_raw = raw_scores.get('BM25', 0)
            bm25_weak = bm25_raw < 5.0  # Weak match threshold for raw score
        else:
            bm25_weak = model_scores.get('BM25', 0) < 0.2

        if semantic > 0.7 and bm25_weak:
            return "Semantic successfully matches cross-lingual entities; lexical models fail"
        elif fuzzy > 50:  # Fuzzy scores are 0-100
            return "Fuzzy matching provides partial entity matching through character similarity"
        else:
            return "All models struggle with entity matching"

    def _generate_semantic_lexical_case_study(self, query, winner, all_results):
        """Generate detailed case study for semantic vs lexical"""
        case_study = {
            'query': query,
            'winner': winner,
            'top_results': {}
        }

        # Get top result from each model with both normalized and raw scores
        for model_name in ['BM25', 'Semantic']:
            if model_name in all_results and all_results[model_name]:
                top = all_results[model_name][0]
                case_study['top_results'][model_name] = {
                    'title': top.get('doc', {}).get('title', 'N/A'),
                    'score': top.get('score', 0),
                    'raw_score': self._get_score(top, prefer_raw=True)
                }

        return case_study

    def _assess_cross_script_handling(self, variant_scores, best_variants):
        """Assess how well system handles cross-script variants"""
        analysis = []

        # Check if different models prefer different variants
        unique_best = len(set(best_variants.values()))

        if unique_best == 1:
            analysis.append(f"All models perform best with variant: {list(best_variants.values())[0]}")
        else:
            analysis.append("Different models prefer different variants:")
            for model, variant in best_variants.items():
                analysis.append(f"  {model}: {variant}")

        # Check semantic model performance
        if 'Semantic' in best_variants:
            analysis.append("Semantic model shows more flexibility with script variations")

        return " ".join(analysis)

    def generate_error_report(self):
        """
        Generate comprehensive error analysis report

        Returns:
            dict: Complete error report
                {
                    'total_cases': int,
                    'categories': {...},
                    'summary': str,
                    'recommendations': [...]
                }
        """
        total_cases = sum(len(cases) for cases in self.categories.values())

        # Generate summary
        summary = self._generate_summary()

        # Generate recommendations
        recommendations = self._generate_recommendations()

        return {
            'total_cases': total_cases,
            'categories': self.categories,
            'summary': summary,
            'recommendations': recommendations,
            'category_counts': {
                cat: len(cases) for cat, cases in self.categories.items()
            }
        }

    def _generate_summary(self):
        """Generate summary of error analysis"""
        summaries = []

        # Count cases per category
        for category, cases in self.categories.items():
            if cases:
                summaries.append(f"{category.replace('_', ' ').title()}: {len(cases)} case(s) analyzed")

        # Overall insight
        semantic_wins = sum(1 for c in self.categories['semantic_vs_lexical'] if c.get('semantic_wins'))
        lexical_wins = sum(1 for c in self.categories['semantic_vs_lexical'] if c.get('lexical_wins'))

        if semantic_wins > lexical_wins:
            summaries.append(f"\nSemantic models significantly outperform lexical models for cross-lingual queries ({semantic_wins} vs {lexical_wins})")
        elif lexical_wins > semantic_wins:
            summaries.append(f"\nLexical models perform better for monolingual exact-match queries ({lexical_wins} vs {semantic_wins})")

        return "\n".join(summaries)

    def _generate_recommendations(self):
        """Generate actionable recommendations"""
        recommendations = [
            "Implement NER mapping layer for cross-lingual entity matching",
            "Add transliteration preprocessing to normalize script variants",
            "Use hybrid approach: Semantic for cross-lingual + Lexical for exact matching",
            "Validate translation quality for common query terms using dictionary",
            "Leverage language-agnostic embeddings (LaBSE) for code-switching queries"
        ]
        return recommendations

    def save_report(self, output_file):
        """
        Save error analysis report to JSON

        Args:
            output_file (str): Path to output file
        """
        report = self.generate_error_report()

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f" Error analysis report saved to {output_file}")

    def print_report(self):
        """Print formatted error analysis report"""
        report = self.generate_error_report()

        print(f"\n{'=' * 80}")
        print("ERROR ANALYSIS REPORT")
        print(f"{'=' * 80}")
        print(f"Total Cases Analyzed: {report['total_cases']}\n")

        for category, cases in report['categories'].items():
            if cases:
                print(f"\n{category.upper().replace('_', ' ')}")
                print(f"{'-' * 70}")
                for case in cases:
                    print(f"  Query: {case.get('query', case.get('query_original', 'N/A'))}")
                    print(f"  Analysis: {case.get('analysis', case.get('impact', case.get('reason', 'N/A')))}")
                    print()

        print(f"\n{'=' * 80}")
        print("SUMMARY")
        print(f"{'=' * 80}")
        print(report['summary'])

        print(f"\n{'=' * 80}")
        print("RECOMMENDATIONS")
        print(f"{'=' * 80}")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")

        print(f"{'=' * 80}\n")


if __name__ == "__main__":
    # Test the error analyzer
    print("Testing ErrorAnalyzer...")

    analyzer = ErrorAnalyzer()

    # Test 1: Translation Failure
    print("\n[Test 1] Translation Failure:")
    analyzer.analyze_translation_failures(
        query="চেয়ার",
        translation_data={
            'original': 'চেয়ার',
            'translated': 'Chairman',
            'method': 'google_translate',
            'expected': 'chair'
        },
        retrieval_results={
            'BM25': [{'score': 0.05}],
            'Semantic': [{'score': 0.65}]
        }
    )

    # Test 2: Entity Mismatch
    print("[Test 2] Entity Mismatch:")
    analyzer.analyze_entity_mismatch(
        query="ঢাকা economy",
        entities=[{'text': 'ঢাকা', 'type': 'GPE', 'variants': ['Dhaka', 'Dacca']}],
        retrieval_results={
            'BM25': [{'score': 0.0}],
            'Fuzzy': [{'score': 0.65}],
            'Semantic': [{'score': 0.89}]
        }
    )

    # Test 3: Semantic vs Lexical
    print("[Test 3] Semantic vs Lexical:")
    analyzer.analyze_semantic_lexical_wins(
        query="শিক্ষা",
        all_results={
            'BM25': [{'score': 0.0, 'doc': {'title': 'No match'}}],
            'Semantic': [{'score': 0.87, 'doc': {'title': 'স্কুল system'}}]
        }
    )

    # Print report
    analyzer.print_report()

    print("\n✓ ErrorAnalyzer test passed!")
