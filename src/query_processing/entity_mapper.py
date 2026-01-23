"""Named entity recognition and cross-lingual mapping using spaCy with Gemini fallback"""

from ..utils.logger import setup_logger
from ..utils import gemini_api


class EntityMapper:
    """
    Extract and map named entities across languages

    Methods:
    1. spaCy NER - for entity extraction
    2. Cross-lingual mapping dictionary - for translation of entities
    """

    # Cross-lingual entity mappings (for translating recognized entities)
    # This is necessary because NER models extract entities but don't translate them
    CROSS_LINGUAL_MAP = {
        # Countries
        'bangladesh': 'বাংলাদেশ', 'india': 'ভারত', 'pakistan': 'পাকিস্তান',
        'china': 'চীন', 'usa': 'যুক্তরাষ্ট্র', 'united states': 'যুক্তরাষ্ট্র',
        'uk': 'যুক্তরাজ্য', 'united kingdom': 'যুক্তরাজ্য',
        'japan': 'জাপান', 'australia': 'অস্ট্রেলিয়া',

        # Major cities
        'dhaka': 'ঢাকা', 'chittagong': 'চট্টগ্রাম', 'sylhet': 'সিলেট',
        'rajshahi': 'রাজশাহী', 'khulna': 'খুলনা', 'comilla': 'কুমিল্লা',
        'rangpur': 'রংপুর', 'barisal': 'বরিশাল', 'kolkata': 'কলকাতা',
        'delhi': 'দিল্লি', 'mumbai': 'মুম্বাই',

        # Organizations
        'dhaka university': 'ঢাকা বিশ্ববিদ্যালয়',
        'university of dhaka': 'ঢাকা বিশ্ববিদ্যালয়',
        'buet': 'বুয়েট', 'brac': 'ব্র্যাক',
        'grameen bank': 'গ্রামীণ ব্যাংক',
    }

    def __init__(self, spacy_model='en_core_web_sm', use_gemini_fallback=True):
        """
        Initialize entity mapper with spaCy and optional Gemini fallback

        Args:
            spacy_model: spaCy model name (default: en_core_web_sm)
            use_gemini_fallback: Whether to use Gemini API as fallback
        """
        self.logger = setup_logger('EntityMapper')
        self.spacy_model_name = spacy_model
        self.method_used = None

        # Check spaCy availability
        self._spacy_available = self._check_spacy()
        self._nlp = None  # Lazy loaded

        # Check Gemini availability
        self._use_gemini = use_gemini_fallback
        self._gemini_available = gemini_api.is_available() if use_gemini_fallback else False

        # Build reverse mapping
        self.en_to_bn = self.CROSS_LINGUAL_MAP
        self.bn_to_en = {v: k for k, v in self.CROSS_LINGUAL_MAP.items()}

        methods = []
        if self._spacy_available:
            methods.append('spaCy NER')
        methods.append('Dictionary')
        if self._gemini_available:
            methods.append('Gemini API')

        self.logger.info(f"EntityMapper initialized. Available: {', '.join(methods)}")

    def _check_spacy(self):
        """Check if spaCy and model are available"""
        try:
            import spacy
            return True
        except ImportError:
            return False

    def _get_nlp(self):
        """Lazy load spaCy model"""
        if self._nlp is None and self._spacy_available:
            import spacy
            try:
                self._nlp = spacy.load(self.spacy_model_name)
                self.logger.info(f"Loaded spaCy model: {self.spacy_model_name}")
            except OSError:
                # Model not installed, try to download
                self.logger.info(f"Downloading spaCy model: {self.spacy_model_name}")
                try:
                    from spacy.cli import download
                    download(self.spacy_model_name)
                    self._nlp = spacy.load(self.spacy_model_name)
                except Exception as e:
                    self.logger.warning(f"Failed to load spaCy model: {e}")
                    self._spacy_available = False
                    return None
        return self._nlp

    def extract_entities(self, text, language='english'):
        """
        Extract named entities from text using spaCy, dictionary, and Gemini fallback

        Args:
            text: Input text
            language: 'english' or 'bangla'

        Returns:
            List of dicts with entity info and extraction method
        """
        entities = []

        # Try spaCy first for English
        if self._spacy_available and language == 'english':
            spacy_entities = self._extract_with_spacy(text)
            if spacy_entities:
                entities.extend(spacy_entities)
                self.method_used = 'spacy_ner'

        # Also check our dictionary for known entities (both languages)
        dict_entities = self._extract_with_dictionary(text, language)
        if dict_entities:
            # Add only entities not already found by spaCy
            existing_texts = {e['text'].lower() for e in entities}
            for ent in dict_entities:
                if ent['text'].lower() not in existing_texts:
                    entities.append(ent)

            if not entities or self.method_used != 'spacy_ner':
                self.method_used = 'dictionary'
            else:
                self.method_used = 'spacy_ner+dictionary'

        # Fallback to Gemini if no entities found and Gemini is available
        if not entities and self._gemini_available:
            gemini_entities = gemini_api.extract_entities(text, language)
            if gemini_entities:
                entities.extend(gemini_entities)
                self.method_used = 'gemini_ner'
                self.logger.debug(f"Used Gemini fallback for entity extraction: {len(gemini_entities)} entities")

        if not entities:
            self.method_used = 'none'

        return entities

    def _extract_with_spacy(self, text):
        """Extract entities using spaCy NER"""
        nlp = self._get_nlp()
        if nlp is None:
            return []

        try:
            doc = nlp(text)
            entities = []

            for ent in doc.ents:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'method': 'spacy_ner'
                })

            return entities

        except Exception as e:
            self.logger.warning(f"spaCy NER failed: {e}")
            return []

    def _extract_with_dictionary(self, text, language):
        """Extract known entities using dictionary matching"""
        entities = []
        text_lower = text.lower()

        # Select dictionary based on language
        if language == 'english':
            dictionary = self.en_to_bn
        else:
            dictionary = self.bn_to_en

        for entity in dictionary.keys():
            # Case-insensitive search
            if entity.lower() in text_lower or entity in text:
                # Find position
                start = text_lower.find(entity.lower())
                if start == -1:
                    start = text.find(entity)

                entities.append({
                    'text': entity,
                    'label': 'ENTITY',  # Generic label for dictionary matches
                    'start': start if start >= 0 else 0,
                    'end': (start + len(entity)) if start >= 0 else len(entity),
                    'method': 'dictionary'
                })

        return entities

    def extract_and_map(self, text, source_lang, target_lang):
        """
        Extract entities and map them to target language

        Args:
            text: Input text
            source_lang: Source language
            target_lang: Target language

        Returns:
            List of dicts with original, mapped, and method info
        """
        # Extract entities
        entities = self.extract_entities(text, source_lang)

        # Map to target language
        mapped_entities = []
        for ent in entities:
            mapped = self.map_entity(ent['text'], source_lang, target_lang)
            mapped_entities.append({
                'original': ent['text'],
                'mapped': mapped,
                'label': ent['label'],
                'source_lang': source_lang,
                'target_lang': target_lang,
                'extraction_method': ent['method'],
                'mapping_method': 'cross_lingual_dict' if mapped != ent['text'] else 'none'
            })

        return mapped_entities

    def map_entity(self, entity, source_lang, target_lang):
        """
        Map entity to target language using dictionary or Gemini fallback

        Args:
            entity: Entity text
            source_lang: 'bangla' or 'english'
            target_lang: 'bangla' or 'english'

        Returns:
            Mapped entity (or original if not found)
        """
        if source_lang == target_lang:
            return entity

        entity_lower = entity.lower()
        mapped = None

        if source_lang == 'english' and target_lang == 'bangla':
            mapped = self.en_to_bn.get(entity_lower)
        elif source_lang == 'bangla' and target_lang == 'english':
            # For Bangla, try exact match first
            mapped = self.bn_to_en.get(entity)

        # If dictionary mapping found, return it
        if mapped:
            return mapped

        # Fallback to Gemini if available and dictionary didn't have mapping
        if self._gemini_available:
            gemini_mapped = gemini_api.map_entity(entity, source_lang, target_lang)
            if gemini_mapped and gemini_mapped != entity:
                self.logger.debug(f"Used Gemini fallback to map entity: {entity} -> {gemini_mapped}")
                return gemini_mapped

        return entity

    def get_all_variants(self, entity):
        """
        Get all language variants of an entity

        Args:
            entity: Entity text

        Returns:
            List of all variants
        """
        variants = [entity]
        entity_lower = entity.lower()

        # Check English -> Bangla
        if entity_lower in self.en_to_bn:
            variants.append(self.en_to_bn[entity_lower])

        # Check Bangla -> English
        if entity in self.bn_to_en:
            variants.append(self.bn_to_en[entity])

        return list(set(variants))

    def add_mapping(self, english, bangla):
        """
        Add custom entity mapping

        Args:
            english: English entity
            bangla: Bangla entity
        """
        self.en_to_bn[english.lower()] = bangla
        self.bn_to_en[bangla] = english.lower()
        self.logger.debug(f"Added mapping: {english} <-> {bangla}")

    def get_method_used(self):
        """Return method used for last extraction"""
        return self.method_used

    def get_available_methods(self):
        """Return dict of available extraction methods"""
        return {
            'spacy_ner': self._spacy_available,
            'dictionary': True,
            'gemini_ner': self._gemini_available
        }

    def get_entity_types(self):
        """Return spaCy entity types if available"""
        if self._spacy_available:
            return [
                'PERSON', 'NORP', 'FAC', 'ORG', 'GPE', 'LOC',
                'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LAW',
                'LANGUAGE', 'DATE', 'TIME', 'PERCENT', 'MONEY',
                'QUANTITY', 'ORDINAL', 'CARDINAL'
            ]
        return ['ENTITY']

    def is_known_entity(self, text):
        """
        Check if text is a known entity in our mappings

        Args:
            text: Text to check

        Returns:
            Boolean
        """
        text_lower = text.lower()
        return text_lower in self.en_to_bn or text in self.bn_to_en

    def get_mapping_count(self):
        """Get number of cross-lingual mappings"""
        return len(self.CROSS_LINGUAL_MAP)
