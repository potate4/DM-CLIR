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

    def analyze_translation_failures(self, query, translation_data, retrieval_results):
        """
        Category 1: Translation Failures

        Example: "�ǯ���" (chair) � "Chairman" (incorrect translation)
        Results in retrieving irrelevant documents

        Args:
            query (str): Original query
            translation_data (dict): Translation information
                {
                    'original': '�ǯ���',
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

        # Check if BM25 failed due to bad translation
        bm25_top_score = 0
        if 'BM25' in retrieval_results and retrieval_results['BM25']:
            bm25_top_score = retrieval_results['BM25'][0].get('score', 0)

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
            'semantic_top_score': semantic_top_score,
            'impact': self._assess_translation_impact(bm25_top_score, semantic_top_score),
            'recommendation': 'Use dictionary for common words or verify translation quality'
        }

        self.categories['translation_failures'].append(case)
        return case

    def analyze_entity_mismatch(self, query, entities, retrieval_results):
        """
        Category 2: Named Entity Mismatch

        Example: Query has "����" (Dhaka in Bangla), documents have "Dhaka" (English)
        Lexical models fail to match, semantic models succeed

        Args:
            query (str): Query text
            entities (list): List of detected entities
                [{'text': '����', 'type': 'GPE', 'variants': ['Dhaka', 'Dacca']}, ...]
            retrieval_results (dict): Results from all models

        Returns:
            dict: Analysis of entity mismatch
        """
        if not entities:
            return None

        # Get scores from different models
        model_scores = {}
        for model_name in ['BM25', 'Fuzzy', 'Semantic']:
            if model_name in retrieval_results and retrieval_results[model_name]:
                model_scores[model_name] = retrieval_results[model_name][0].get('score', 0)

        case = {
            'category': 'named_entity_mismatch',
            'query': query,
            'entities': entities,
            'model_scores': model_scores,
            'bm25_score': model_scores.get('BM25', 0),
            'fuzzy_score': model_scores.get('Fuzzy', 0),
            'semantic_score': model_scores.get('Semantic', 0),
            'analysis': self._assess_entity_matching(model_scores),
            'recommendation': 'Add NER mapping layer to handle cross-lingual entity matching'
        }

        self.categories['named_entity_mismatch'].append(case)
        return case

    def analyze_semantic_lexical_wins(self, query, all_results):
        """
        Category 3: Semantic vs Lexical Wins

        Example: Query "���ͷ�" (education), BM25=0 (no match), Semantic retrieves "�͕��" (school)

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
        # Get top scores
        lexical_score = 0  # Max of BM25, TF-IDF
        semantic_score = 0

        if 'BM25' in all_results and all_results['BM25']:
            lexical_score = max(lexical_score, all_results['BM25'][0].get('score', 0))

        if 'TF-IDF' in all_results and all_results['TF-IDF']:
            lexical_score = max(lexical_score, all_results['TF-IDF'][0].get('score', 0))

        if 'Semantic' in all_results and all_results['Semantic']:
            semantic_score = all_results['Semantic'][0].get('score', 0)

        # Determine winner
        score_diff = semantic_score - lexical_score

        if score_diff > 0.3:
            winner = 'semantic'
            reason = 'Cross-lingual semantic matching; lexical models failed due to script/language mismatch'
        elif score_diff < -0.3:
            winner = 'lexical'
            reason = 'Exact term matching; query and documents share common terms'
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
            'semantic_top_score': semantic_score,
            'score_difference': score_diff,
            'case_study': self._generate_semantic_lexical_case_study(query, winner, all_results)
        }

        self.categories['semantic_vs_lexical'].append(case)
        return case

    def analyze_cross_script_ambiguity(self, query_variants, retrieval_results_per_variant):
        """
        Category 4: Cross-Script Ambiguity

        Example: "Bangladesh" vs "������Ƕ" vs "Bangla Desh" (two words)
        Which transliterations work with which models?

        Args:
            query_variants (list): List of query variants
                ['Bangladesh', '������Ƕ', 'Bangla Desh']
            retrieval_results_per_variant (dict): Results for each variant
                {
                    'Bangladesh': {'BM25': [...], 'Semantic': [...]},
                    '������Ƕ': {...},
                    'Bangla Desh': {...}
                }

        Returns:
            dict: Analysis of cross-script handling
        """
        # Aggregate scores for each variant across models
        variant_scores = {}

        for variant in query_variants:
            if variant not in retrieval_results_per_variant:
                continue

            results = retrieval_results_per_variant[variant]
            variant_scores[variant] = {}

            for model_name in ['BM25', 'Fuzzy', 'Semantic']:
                if model_name in results and results[model_name]:
                    variant_scores[variant][model_name] = results[model_name][0].get('score', 0)

        # Find best variant for each model
        best_variants = {}
        for model_name in ['BM25', 'Fuzzy', 'Semantic']:
            best_score = 0
            best_variant = None

            for variant, scores in variant_scores.items():
                score = scores.get(model_name, 0)
                if score > best_score:
                    best_score = score
                    best_variant = variant

            best_variants[model_name] = best_variant

        case = {
            'category': 'cross_script_ambiguity',
            'query_variants': query_variants,
            'variant_scores': variant_scores,
            'best_variant_per_model': best_variants,
            'analysis': self._assess_cross_script_handling(variant_scores, best_variants),
            'recommendation': 'Add transliteration preprocessing to normalize variants'
        }

        self.categories['cross_script_ambiguity'].append(case)
        return case

    def analyze_code_switching(self, query, language_mix, retrieval_results):
        """
        Category 5: Code-Switching

        Example: "Bangladesh � cricket �ǲ�" (mixes English and Bangla)
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
        # Get scores
        model_scores = {}
        for model_name in ['BM25', 'TF-IDF', 'Fuzzy', 'Semantic']:
            if model_name in retrieval_results and retrieval_results[model_name]:
                model_scores[model_name] = retrieval_results[model_name][0].get('score', 0)

        # Assess handling quality
        bm25_score = model_scores.get('BM25', 0)
        semantic_score = model_scores.get('Semantic', 0)

        if semantic_score > bm25_score + 0.2:
            handling = 'good'
            analysis = 'Semantic model handles code-switching better than lexical'
        elif bm25_score > 0.3:
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
            'bm25_score': bm25_score,
            'semantic_score': semantic_score,
            'handling_quality': handling,
            'analysis': analysis,
            'recommendation': 'Language-agnostic embeddings (like LaBSE) help with code-switching'
        }

        self.categories['code_switching'].append(case)
        return case

    def _assess_translation_impact(self, bm25_score, semantic_score):
        """Assess impact of translation quality"""
        if bm25_score < 0.1 and semantic_score > 0.5:
            return "High impact: Bad translation caused BM25 failure, but Semantic succeeded"
        elif bm25_score < 0.1:
            return "Critical impact: Bad translation caused complete retrieval failure"
        else:
            return "Low impact: Translation quality did not significantly affect retrieval"

    def _assess_entity_matching(self, model_scores):
        """Assess entity matching across models"""
        bm25 = model_scores.get('BM25', 0)
        fuzzy = model_scores.get('Fuzzy', 0)
        semantic = model_scores.get('Semantic', 0)

        if semantic > 0.7 and bm25 < 0.2:
            return "Semantic successfully matches cross-lingual entities; lexical models fail"
        elif fuzzy > 0.5:
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

        # Get top result from each model
        for model_name in ['BM25', 'Semantic']:
            if model_name in all_results and all_results[model_name]:
                top = all_results[model_name][0]
                case_study['top_results'][model_name] = {
                    'title': top.get('doc', {}).get('title', 'N/A'),
                    'score': top.get('score', 0)
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
        query="�ǯ���",
        translation_data={
            'original': '�ǯ���',
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
        query="���� economy",
        entities=[{'text': '����', 'type': 'GPE', 'variants': ['Dhaka', 'Dacca']}],
        retrieval_results={
            'BM25': [{'score': 0.0}],
            'Fuzzy': [{'score': 0.65}],
            'Semantic': [{'score': 0.89}]
        }
    )

    # Test 3: Semantic vs Lexical
    print("[Test 3] Semantic vs Lexical:")
    analyzer.analyze_semantic_lexical_wins(
        query="���ͷ�",
        all_results={
            'BM25': [{'score': 0.0, 'doc': {'title': 'No match'}}],
            'Semantic': [{'score': 0.87, 'doc': {'title': '�͕�� system'}}]
        }
    )

    # Print report
    analyzer.print_report()

    print("\n ErrorAnalyzer test passed!")
