"""
Confidence Scorer
Evaluates retrieval confidence and generates warnings for low-quality results
"""


class ConfidenceScorer:
    """
    Evaluate retrieval confidence and generate warnings for low-quality matches
    """

    # Default threshold for low confidence warning
    LOW_CONFIDENCE_THRESHOLD = 0.20

    def __init__(self, threshold=None):
        """
        Initialize confidence scorer

        Args:
            threshold (float): Confidence threshold (default: 0.20)
        """
        self.threshold = threshold if threshold is not None else self.LOW_CONFIDENCE_THRESHOLD

    def evaluate_confidence(self, ranked_results):
        """
        Check if top result has low confidence

        Args:
            ranked_results (dict): Output from DocumentRanker.rank_documents()
                {
                    'model': str,
                    'results': [{'score': float, 'doc': {...}, 'rank': int}, ...]
                }

        Returns:
            dict: Confidence evaluation
                {
                    'is_low_confidence': bool,
                    'top_score': float,
                    'warning_message': str or None,
                    'recommendation': str or None,
                    'threshold': float
                }
        """
        if not ranked_results.get('results'):
            return {
                'is_low_confidence': True,
                'top_score': 0.0,
                'warning_message': self._generate_warning(None, 0.0, ranked_results.get('model', 'Unknown')),
                'recommendation': 'No results found. Try rephrasing your query.',
                'threshold': self.threshold
            }

        top_result = ranked_results['results'][0]
        top_score = top_result['score']
        model = ranked_results.get('model', 'Unknown')

        if top_score < self.threshold:
            return {
                'is_low_confidence': True,
                'top_score': top_score,
                'warning_message': self._generate_warning(None, top_score, model),
                'recommendation': self._generate_recommendation(top_score, model),
                'threshold': self.threshold
            }

        return {
            'is_low_confidence': False,
            'top_score': top_score,
            'warning_message': None,
            'recommendation': None,
            'threshold': self.threshold
        }

    def _generate_warning(self, query, score, model):
        """
        Generate user-friendly warning message

        Args:
            query (str): Query text (optional)
            score (float): Top result score
            model (str): Model name

        Returns:
            str: Warning message
        """
        warning = f"� Warning: Retrieved results may not be relevant. Matching confidence\n"
        warning += f"is low (score: {score:.2f}).\n"
        warning += f"Consider rephrasing your query or checking translation quality."

        return warning

    def _generate_recommendation(self, score, model):
        """
        Generate model-specific recommendation

        Args:
            score (float): Top result score
            model (str): Model name

        Returns:
            str: Recommendation text
        """
        recommendations = {
            'BM25': 'Try using different keywords or check if translation is accurate.',
            'TF-IDF': 'Try using different keywords or check if translation is accurate.',
            'Fuzzy': 'Check for spelling errors or try different query formulation.',
            'Semantic': 'Try rephrasing the query or using more specific terms.'
        }

        default_rec = 'Try rephrasing your query with different words.'
        return recommendations.get(model, default_rec)

    def evaluate_all_models(self, all_results):
        """
        Evaluate confidence for all models

        Args:
            all_results (dict): Results from all models
                {
                    'BM25': {'results': [...]},
                    'Semantic': {'results': [...]},
                    ...
                }

        Returns:
            dict: Confidence evaluation for each model
                {
                    'BM25': {'is_low_confidence': True, ...},
                    'Semantic': {'is_low_confidence': False, ...},
                    'overall_confidence': 'low'|'medium'|'high',
                    'best_model': 'Semantic'
                }
        """
        evaluations = {}
        best_score = 0.0
        best_model = None

        for model_name, results in all_results.items():
            evaluation = self.evaluate_confidence(results)
            evaluations[model_name] = evaluation

            if evaluation['top_score'] > best_score:
                best_score = evaluation['top_score']
                best_model = model_name

        # Determine overall confidence
        if best_score < self.threshold:
            overall = 'low'
        elif best_score < 0.5:
            overall = 'medium'
        else:
            overall = 'high'

        evaluations['overall_confidence'] = overall
        evaluations['best_model'] = best_model
        evaluations['best_score'] = best_score

        return evaluations

    def print_warning(self, confidence_eval):
        """
        Print warning message to console

        Args:
            confidence_eval (dict): Output from evaluate_confidence()
        """
        if confidence_eval['is_low_confidence']:
            print("\n" + "=" * 80)
            print(confidence_eval['warning_message'])
            if confidence_eval['recommendation']:
                print(f"\nRecommendation: {confidence_eval['recommendation']}")
            print("=" * 80 + "\n")


if __name__ == "__main__":
    # Test the scorer
    print("Testing ConfidenceScorer...")

    scorer = ConfidenceScorer(threshold=0.20)

    # Test case 1: Low confidence
    print("\n[Test 1] Low confidence result:")
    low_confidence_result = {
        'model': 'BM25',
        'results': [
            {'score': 0.15, 'doc': {'title': 'Irrelevant doc'}, 'rank': 1},
            {'score': 0.10, 'doc': {'title': 'Another doc'}, 'rank': 2}
        ]
    }
    eval1 = scorer.evaluate_confidence(low_confidence_result)
    print(f"Is low confidence: {eval1['is_low_confidence']}")
    print(f"Top score: {eval1['top_score']:.3f}")
    scorer.print_warning(eval1)

    # Test case 2: High confidence
    print("\n[Test 2] High confidence result:")
    high_confidence_result = {
        'model': 'Semantic',
        'results': [
            {'score': 0.92, 'doc': {'title': 'Relevant doc'}, 'rank': 1},
            {'score': 0.85, 'doc': {'title': 'Another doc'}, 'rank': 2}
        ]
    }
    eval2 = scorer.evaluate_confidence(high_confidence_result)
    print(f"Is low confidence: {eval2['is_low_confidence']}")
    print(f"Top score: {eval2['top_score']:.3f}")
    if not eval2['is_low_confidence']:
        print(" High confidence - no warning needed")

    # Test case 3: Multiple models
    print("\n[Test 3] Multiple models:")
    all_results = {
        'BM25': low_confidence_result,
        'Semantic': high_confidence_result
    }
    all_eval = scorer.evaluate_all_models(all_results)
    print(f"Overall confidence: {all_eval['overall_confidence']}")
    print(f"Best model: {all_eval['best_model']} (score: {all_eval['best_score']:.3f})")

    print("\n ConfidenceScorer test passed!")
