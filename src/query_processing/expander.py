"""Query expansion using WordNet, embeddings, stemming, and lemmatization"""

from ..utils.logger import setup_logger


class QueryExpander:
    """
    Expand queries with synonyms and related terms

    Methods (in order of preference):
    1. WordNet (English) - via NLTK
    2. Word embeddings similarity - via gensim/sentence-transformers
    3. Stemming/Lemmatization - via NLTK
    4. Dictionary fallback (Bangla, last resort)
    """

    # Minimal Bangla fallback (no good WordNet for Bangla)
    BANGLA_FALLBACK = {
        'শিক্ষা': ['বিদ্যা', 'পড়াশোনা'],
        'সরকার': ['প্রশাসন', 'শাসন'],
        'রাজনীতি': ['রাজনৈতিক'],
        'খেলা': ['খেলাধুলা', 'ক্রীড়া'],
        'স্বাস্থ্য': ['চিকিৎসা'],
        'সংবাদ': ['খবর'],
    }

    def __init__(self, max_expansions=5, use_embeddings=True):
        """
        Initialize expander with available backends

        Args:
            max_expansions: Maximum synonyms per term
            use_embeddings: Whether to use word embeddings for similarity
        """
        self.logger = setup_logger('QueryExpander')
        self.max_expansions = max_expansions
        self.use_embeddings = use_embeddings
        self.methods_used = {}

        # Check available backends
        self._wordnet_available = self._check_wordnet()
        self._embeddings_available = self._check_embeddings() if use_embeddings else False
        self._nltk_available = self._check_nltk()

        # Lazy loaded resources
        self._lemmatizer = None
        self._stemmer = None
        self._embedding_model = None

        methods = []
        if self._wordnet_available:
            methods.append('WordNet')
        if self._embeddings_available:
            methods.append('Embeddings')
        if self._nltk_available:
            methods.append('Stemming/Lemma')
        methods.append('Dictionary')

        self.logger.info(f"QueryExpander initialized. Available: {', '.join(methods)}")

    def _check_wordnet(self):
        """Check if NLTK WordNet is available"""
        try:
            from nltk.corpus import wordnet
            # Try to access wordnet to ensure data is downloaded
            wordnet.synsets('test')
            return True
        except Exception:
            try:
                import nltk
                nltk.download('wordnet', quiet=True)
                nltk.download('omw-1.4', quiet=True)
                from nltk.corpus import wordnet
                wordnet.synsets('test')
                return True
            except Exception:
                return False

    def _check_embeddings(self):
        """Check if word embedding library is available"""
        try:
            from gensim.models import KeyedVectors
            return True
        except ImportError:
            try:
                from sentence_transformers import SentenceTransformer
                return True
            except ImportError:
                return False

    def _check_nltk(self):
        """Check if NLTK stemmer/lemmatizer is available"""
        try:
            from nltk.stem import WordNetLemmatizer, PorterStemmer
            return True
        except ImportError:
            try:
                import nltk
                nltk.download('wordnet', quiet=True)
                from nltk.stem import WordNetLemmatizer, PorterStemmer
                return True
            except Exception:
                return False

    def _get_lemmatizer(self):
        """Get or create lemmatizer"""
        if self._lemmatizer is None and self._nltk_available:
            from nltk.stem import WordNetLemmatizer
            self._lemmatizer = WordNetLemmatizer()
        return self._lemmatizer

    def _get_stemmer(self):
        """Get or create stemmer"""
        if self._stemmer is None and self._nltk_available:
            from nltk.stem import PorterStemmer
            self._stemmer = PorterStemmer()
        return self._stemmer

    def expand(self, query, language=None):
        """
        Expand query with synonyms using multiple methods

        Args:
            query: Query string
            language: 'bangla' or 'english' (auto-detect if None)

        Returns:
            Dict with:
                - expansions: {word: [synonyms]}
                - methods: {word: method_used}
        """
        if not query:
            return {'expansions': {}, 'methods': {}}

        words = query.split()
        expansions = {}
        methods = {}

        for word in words:
            word_lower = word.lower()
            synonyms, method = self._get_synonyms_with_method(word, word_lower, language)

            # Include original word + synonyms (limited)
            all_terms = [word] + synonyms[:self.max_expansions]
            expansions[word] = list(dict.fromkeys(all_terms))  # Remove duplicates, keep order
            methods[word] = method

        self.methods_used = methods
        return {'expansions': expansions, 'methods': methods}

    def _get_synonyms_with_method(self, word, word_lower, language):
        """
        Get synonyms for a word, trying multiple methods

        Returns:
            (list of synonyms, method used)
        """
        synonyms = []
        method = 'none'

        # For English
        if language in [None, 'english', 'mixed']:
            # 1. Try WordNet
            if self._wordnet_available:
                wn_synonyms = self._wordnet_synonyms(word_lower)
                if wn_synonyms:
                    synonyms.extend(wn_synonyms)
                    method = 'wordnet'

            # 2. Try embeddings if WordNet didn't find much
            if len(synonyms) < 2 and self._embeddings_available:
                emb_synonyms = self._embedding_synonyms(word_lower)
                if emb_synonyms:
                    synonyms.extend(emb_synonyms)
                    method = 'embeddings' if not synonyms else f'{method}+embeddings'

            # 3. Add lemma/stem variants
            if self._nltk_available:
                variants = self._get_morphological_variants(word_lower)
                if variants:
                    synonyms.extend(variants)
                    if method == 'none':
                        method = 'stemming'
                    else:
                        method = f'{method}+stemming'

        # For Bangla - use fallback dictionary
        if language in [None, 'bangla', 'mixed']:
            if word in self.BANGLA_FALLBACK:
                synonyms.extend(self.BANGLA_FALLBACK[word])
                method = 'dictionary_fallback' if method == 'none' else f'{method}+dictionary'

        if not synonyms:
            method = 'none'

        return list(dict.fromkeys(synonyms)), method  # Remove duplicates

    def _wordnet_synonyms(self, word):
        """Get synonyms from WordNet"""
        try:
            from nltk.corpus import wordnet

            synonyms = set()
            for syn in wordnet.synsets(word):
                for lemma in syn.lemmas():
                    name = lemma.name().replace('_', ' ').lower()
                    if name != word and len(name) > 2:
                        synonyms.add(name)

            return list(synonyms)[:self.max_expansions * 2]  # Get more, filter later

        except Exception as e:
            self.logger.debug(f"WordNet lookup failed for '{word}': {e}")
            return []

    def _embedding_synonyms(self, word):
        """Get similar words using word embeddings"""
        try:
            # Try gensim first (lighter weight)
            try:
                from gensim.models import KeyedVectors
                import gensim.downloader as api

                if self._embedding_model is None:
                    self.logger.info("Loading word embeddings (glove-wiki-gigaword-50)...")
                    self._embedding_model = api.load('glove-wiki-gigaword-50')

                if word in self._embedding_model:
                    similar = self._embedding_model.most_similar(word, topn=self.max_expansions)
                    return [w for w, _ in similar]
            except Exception:
                pass

            # Fallback to sentence-transformers
            try:
                from sentence_transformers import SentenceTransformer, util
                import torch

                if self._embedding_model is None:
                    self.logger.info("Loading sentence-transformers model...")
                    self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

                # For sentence transformers, we'd need a vocabulary to compare against
                # This is more complex, so skip for now
                pass
            except Exception:
                pass

            return []

        except Exception as e:
            self.logger.debug(f"Embedding lookup failed for '{word}': {e}")
            return []

    def _get_morphological_variants(self, word):
        """Get stem and lemma variants of a word"""
        variants = set()

        try:
            # Lemmatization
            lemmatizer = self._get_lemmatizer()
            if lemmatizer:
                # Try different POS tags
                for pos in ['n', 'v', 'a', 'r']:  # noun, verb, adj, adverb
                    lemma = lemmatizer.lemmatize(word, pos=pos)
                    if lemma != word and len(lemma) > 2:
                        variants.add(lemma)

            # Stemming
            stemmer = self._get_stemmer()
            if stemmer:
                stem = stemmer.stem(word)
                if stem != word and len(stem) > 2:
                    variants.add(stem)

        except Exception as e:
            self.logger.debug(f"Morphological analysis failed for '{word}': {e}")

        return list(variants)

    def expand_to_string(self, query, language=None):
        """
        Expand query and return as string

        Args:
            query: Query string
            language: Language hint

        Returns:
            Expanded query string
        """
        result = self.expand(query, language)
        expansions = result['expansions']

        all_terms = set()
        for terms in expansions.values():
            all_terms.update(terms)

        return ' '.join(all_terms)

    def get_methods_used(self):
        """Return methods used for each word in last expansion"""
        return self.methods_used

    def get_available_methods(self):
        """Return dict of available expansion methods"""
        return {
            'wordnet': self._wordnet_available,
            'embeddings': self._embeddings_available,
            'stemming_lemma': self._nltk_available,
            'dictionary_fallback': True
        }

    def get_wordnet_synonyms(self, word):
        """
        Direct WordNet lookup for a word

        Args:
            word: Word to look up

        Returns:
            List of synonyms from WordNet
        """
        if not self._wordnet_available:
            return []
        return self._wordnet_synonyms(word.lower())

    def get_lemma(self, word, pos='n'):
        """
        Get lemma of a word

        Args:
            word: Word to lemmatize
            pos: Part of speech ('n', 'v', 'a', 'r')

        Returns:
            Lemmatized word
        """
        lemmatizer = self._get_lemmatizer()
        if lemmatizer:
            return lemmatizer.lemmatize(word.lower(), pos=pos)
        return word

    def get_stem(self, word):
        """
        Get stem of a word

        Args:
            word: Word to stem

        Returns:
            Stemmed word
        """
        stemmer = self._get_stemmer()
        if stemmer:
            return stemmer.stem(word.lower())
        return word
