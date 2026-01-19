"""Main query processing pipeline with proper NLP methods"""

from .language_detector import QueryLanguageDetector
from .normalizer import QueryNormalizer
from .translator import QueryTranslator
from .expander import QueryExpander
from .entity_mapper import EntityMapper
from ..utils.logger import setup_logger


class QueryProcessor:
    """
    Complete query processing pipeline for CLIR

    Pipeline:
    1. Language Detection
    2. Normalization
    3. Translation (Google Translate / MarianMT / Dictionary)
    4. Query Expansion (WordNet / Embeddings / Stemming)
    5. Named Entity Mapping (spaCy NER / Dictionary)
    """

    def __init__(self, expand_queries=True, remove_stopwords=False, use_gpu=False):
        """
        Initialize query processor

        Args:
            expand_queries: Whether to expand with synonyms
            remove_stopwords: Whether to remove stopwords
            use_gpu: Whether to use GPU for neural models
        """
        self.logger = setup_logger('QueryProcessor')

        # Initialize components
        self.language_detector = QueryLanguageDetector()
        self.normalizer = QueryNormalizer(remove_stopwords=remove_stopwords)
        self.translator = QueryTranslator(use_gpu=use_gpu)
        self.expander = QueryExpander(use_embeddings=True)
        self.entity_mapper = EntityMapper()

        self.expand_queries = expand_queries

        # Log available methods
        self.logger.info("QueryProcessor initialized")

    def process(self, query):
        """
        Process a query through the full pipeline

        Args:
            query: Raw query string

        Returns:
            Dict with processed query information including methods used
        """
        if not query or not query.strip():
            return self._empty_result()

        result = {
            'original': query,
            'language': None,
            'normalized': None,
            'translated': None,
            'translation_method': None,
            'expanded': {},
            'expansion_methods': {},
            'entities': [],
            'entity_method': None,
            'variants': [],
            'methods_summary': {}
        }

        # Step 1: Language Detection
        language = self.language_detector.detect(query)
        result['language'] = language
        self.logger.info(f"Detected language: {language}")

        # Step 2: Normalization
        normalized = self.normalizer.normalize(query, language)
        result['normalized'] = normalized
        self.logger.info(f"Normalized: {normalized}")

        # Step 3: Translation
        target_lang = 'english' if language == 'bangla' else 'bangla'
        if language in ['bangla', 'english']:
            translated = self.translator.translate(normalized, language, target_lang)
            result['translated'] = translated
            result['translation_method'] = self.translator.get_method_used()
            self.logger.info(f"Translated [{result['translation_method']}]: {len(translated)} chars")
        else:
            result['translated'] = normalized
            result['translation_method'] = 'none'

        # Step 4: Entity Extraction and Mapping
        entities = self.entity_mapper.extract_and_map(normalized, language, target_lang)
        result['entities'] = entities
        result['entity_method'] = self.entity_mapper.get_method_used()
        if entities:
            self.logger.info(f"Found {len(entities)} entities [{result['entity_method']}]")

        # Step 5: Query Expansion
        if self.expand_queries:
            expansion_result = self.expander.expand(normalized, language)
            result['expanded'] = expansion_result['expansions']
            result['expansion_methods'] = expansion_result['methods']

            # Also expand translated query
            if result['translated'] and result['translated'] != normalized:
                translated_expansion = self.expander.expand(result['translated'], target_lang)
                # Merge expansions
                for word, synonyms in translated_expansion['expansions'].items():
                    if word not in result['expanded']:
                        result['expanded'][word] = synonyms
                        result['expansion_methods'][word] = translated_expansion['methods'].get(word, 'none')

            # Log expansion methods
            unique_methods = set(result['expansion_methods'].values())
            if unique_methods:
                self.logger.info(f"Expanded using: {', '.join(unique_methods)}")

        # Generate query variants for retrieval
        result['variants'] = self._generate_variants(result)

        # Summary of methods used
        result['methods_summary'] = {
            'translation': result['translation_method'],
            'entity_extraction': result['entity_method'],
            'expansion': list(set(result['expansion_methods'].values())) if result['expansion_methods'] else []
        }

        return result

    def _generate_variants(self, result):
        """
        Generate query variants for retrieval

        Args:
            result: Processed query result

        Returns:
            List of query variants
        """
        variants = set()

        # Add original normalized query
        if result['normalized']:
            variants.add(result['normalized'])

        # Add translated query
        if result['translated']:
            variants.add(result['translated'])

        # Add entity variants (mapped versions)
        for entity in result['entities']:
            if entity.get('mapped'):
                variants.add(entity['mapped'])

        # Add expanded terms
        for terms in result['expanded'].values():
            for term in terms:
                if isinstance(term, str):
                    variants.add(term)

        return list(variants)

    def _empty_result(self):
        """Return empty result for invalid queries"""
        return {
            'original': '',
            'language': 'unknown',
            'normalized': '',
            'translated': '',
            'translation_method': 'none',
            'expanded': {},
            'expansion_methods': {},
            'entities': [],
            'entity_method': 'none',
            'variants': [],
            'methods_summary': {}
        }

    def get_search_queries(self, query):
        """
        Simple interface to get all search queries

        Args:
            query: Raw query

        Returns:
            List of queries to search for
        """
        result = self.process(query)
        return result['variants']

    def get_available_methods(self):
        """Return all available methods across components"""
        return {
            'translation': self.translator.get_available_methods(),
            'expansion': self.expander.get_available_methods(),
            'entity_extraction': self.entity_mapper.get_available_methods()
        }


# Convenience function
def process_query(query):
    """
    Process a query (convenience function)

    Args:
        query: Raw query string

    Returns:
        Processed query result dict
    """
    processor = QueryProcessor()
    return processor.process(query)
