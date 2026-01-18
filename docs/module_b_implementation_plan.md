# Module B Implementation Plan: Query Processing & Cross-Lingual Handling

## Overview
Module B handles query processing and cross-lingual transformations to enable searching in one language and retrieving results in both languages.

**Marks**: 15%
**Timeline**: Week 1-2 (overlaps with Module A completion)
**Dependencies**: Module A (document indexing)

---

## Phase 1: Language Detection (Day 1)

### 1.1 Query Language Detector

**File**: `src/query_processing/language_detector.py`

**Key Components**:
```python
class QueryLanguageDetector:
    - __init__()
    - detect_language(query)            # Detect query language
    - get_confidence()                  # Confidence score
    - is_bangla(query)                  # Boolean check
    - is_english(query)                 # Boolean check
    - is_mixed(query)                   # Code-switching detection
```

**Implementation**:
```python
def detect_language(self, query):
    """
    Detect language of query
    Returns: 'bangla', 'english', or 'mixed'
    """
    # Use langdetect or character-based detection
    # Bangla Unicode range: \u0980-\u09FF
    # If >50% Bangla chars → bangla
    # If >50% English chars → english
    # Otherwise → mixed
```

**Features**:
- Fast character-based detection for short queries
- Handle code-switching (mixed Bangla-English)
- Confidence threshold: 0.7
- Fallback for ambiguous queries

**Examples**:
```python
detect_language("শিক্ষা")           # → "bangla"
detect_language("education")         # → "english"
detect_language("শিক্ষা education")  # → "mixed"
```

---

## Phase 2: Query Normalization (Day 1-2)

### 2.1 Query Normalizer

**File**: `src/query_processing/normalizer.py`

**Key Components**:
```python
class QueryNormalizer:
    - __init__(language)
    - normalize(query)                  # Main normalization
    - lowercase(text)                   # Lowercase (English)
    - remove_extra_whitespace(text)     # Clean whitespace
    - remove_punctuation(text)          # Optional
    - normalize_unicode(text)           # Unicode normalization (Bangla)
```

**Normalization Steps**:

**For Bangla Queries**:
1. Unicode normalization (NFC)
2. Remove zero-width characters
3. Trim whitespace
4. Optional: Remove punctuation

**For English Queries**:
1. Lowercase conversion
2. Remove extra whitespace
3. Optional: Remove punctuation
4. Optional: Expand contractions

**Examples**:
```python
# Bangla
normalize("  শিক্ষা  ব্যবস্থা  ")  # → "শিক্ষা ব্যবস্থা"

# English
normalize("  EDUCATION System  ")  # → "education system"
normalize("don't stop")             # → "do not stop" (if expanding)
```

### 2.2 Stopword Removal (Optional)

**File**: `src/query_processing/stopword_remover.py`

**Note**: Stopword removal is OPTIONAL for queries (assignment says so)

**Key Components**:
```python
class StopwordRemover:
    - __init__(language)
    - load_stopwords(language)
    - remove_stopwords(tokens)
    - should_remove(word)
```

**Stopword Lists**:
- **English**: Use NLTK stopwords
- **Bangla**: Create custom list (common words like "এবং", "বা", "কিন্তু", etc.)

**When to Use**:
- Long queries (>5 words)
- Might improve precision
- Risk: Might reduce recall

---

## Phase 3: Query Translation (Day 2-3)

### 3.1 Query Translator

**File**: `src/query_processing/translator.py`

**Key Components**:
```python
class QueryTranslator:
    - __init__(translation_service)
    - translate(query, source_lang, target_lang)
    - batch_translate(queries)
    - cache_translation(query, translation)
    - get_cached_translation(query)
```

**Translation Options**:

**Option 1: Google Translate API (Free Tier)**
```python
from deep_translator import GoogleTranslator

translator = GoogleTranslator(source='bn', target='en')
translation = translator.translate("শিক্ষা")
# → "education"
```

**Option 2: Hugging Face Translation Models**
```python
from transformers import pipeline

# OPUS-MT models for Bangla-English
translator = pipeline("translation", model="Helsinki-NLP/opus-mt-bn-en")
translation = translator("শিক্ষা")
# → "education"
```

**Option 3: Custom Dictionary**
- Build custom Bangla-English dictionary
- For common terms and named entities
- Fast lookup, no API calls

**Recommendation**: Start with Google Translate (free), add custom dictionary for important terms

**Translation Strategy**:
1. Detect query language
2. If Bangla → translate to English
3. If English → translate to Bangla
4. If mixed → translate each part separately
5. Cache translations (avoid repeated API calls)

**Error Handling**:
- API failures → use fallback dictionary
- Ambiguous translations → keep multiple options
- Translation quality check → confidence score

**Examples**:
```python
translate("শিক্ষা", "bangla", "english")      # → "education"
translate("education", "english", "bangla")   # → "শিক্ষা"
translate("ঢাকা", "bangla", "english")        # → "Dhaka" (NE)
```

---

## Phase 4: Query Expansion (Day 3-4)

### 4.1 Query Expander

**File**: `src/query_processing/query_expander.py`

**Key Components**:
```python
class QueryExpander:
    - __init__(language)
    - expand(query)                     # Main expansion
    - get_synonyms(word)                # Synonym expansion
    - get_morphological_variants(word)  # Morphology
    - get_transliterations(word)        # Transliteration variants
    - expand_with_embeddings(query)     # Semantic expansion
```

**Expansion Methods**:

#### Method 1: Synonym Expansion
```python
# English: Use WordNet or custom thesaurus
"education" → ["education", "learning", "schooling"]

# Bangla: Custom synonym dictionary
"শিক্ষা" → ["শিক্ষা", "বিদ্যা", "জ্ঞান"]
```

#### Method 2: Morphological Variants
```python
# English: Stemming/lemmatization
"running" → ["run", "running", "runs"]

# Bangla: Root word variants (complex, may skip)
"পড়ছি" → ["পড়া", "পড়ছি", "পড়ব"]
```

#### Method 3: Transliteration Variants
```python
# Important for cross-script matching
"Bangladesh" → ["Bangladesh", "বাংলাদেশ"]
"Dhaka" → ["Dhaka", "ঢাকা", "Dhaka"]
```

#### Method 4: Embedding-Based Expansion
```python
# Use word embeddings to find similar terms
model.most_similar("education") → ["school", "university", "learning"]
```

**Configuration**:
- Max expansions: 3-5 per term
- Expansion weight: Original term weight = 1.0, expanded terms = 0.5-0.8
- Enable/disable per method

**Examples**:
```python
expand("শিক্ষা ব্যবস্থা")
# → {
#     "শিক্ষা": ["শিক্ষা", "বিদ্যা", "education"],
#     "ব্যবস্থা": ["ব্যবস্থা", "সিস্টেম", "system"]
# }
```

### 4.2 Expansion Resources

**Resources Needed**:
1. **English Synonyms**: WordNet (NLTK)
2. **Bangla Synonyms**: Custom dictionary or web scraping
3. **Transliteration Pairs**: Named entity mappings
4. **Embeddings**: Word2Vec or fastText (optional)

---

## Phase 5: Named Entity Mapping (Day 4-5)

### 5.1 Named Entity Recognizer

**File**: `src/query_processing/ne_recognizer.py`

**Key Components**:
```python
class NamedEntityRecognizer:
    - __init__(language)
    - extract_entities(query)           # Extract NEs from query
    - classify_entity(entity)           # Person, Location, Org
    - get_entity_type(entity)
```

**Implementation**:
```python
# English NER: Use spaCy
import spacy
nlp = spacy.load("en_core_web_sm")
doc = nlp("Prime Minister Sheikh Hasina visited Dhaka")
entities = [(ent.text, ent.label_) for ent in doc.ents]
# → [("Sheikh Hasina", "PERSON"), ("Dhaka", "GPE")]

# Bangla NER: Use spaCy multilingual or custom NER
nlp = spacy.load("xx_ent_wiki_sm")  # multilingual
doc = nlp("প্রধানমন্ত্রী শেখ হাসিনা ঢাকা সফর করেন")
entities = [(ent.text, ent.label_) for ent in doc.ents]
```

**Entity Types**:
- PERSON: Person names
- GPE: Geopolitical entities (countries, cities)
- ORG: Organizations
- DATE: Dates
- LOC: Locations

### 5.2 Named Entity Mapper

**File**: `src/query_processing/ne_mapper.py`

**Key Components**:
```python
class NamedEntityMapper:
    - __init__()
    - load_mapping_dictionary()
    - map_entity(entity, source_lang, target_lang)
    - add_mapping(entity_en, entity_bn)
    - get_all_mappings(entity)
```

**Mapping Dictionary**:
```json
{
  "Bangladesh": "বাংলাদেশ",
  "Dhaka": "ঢাকা",
  "Sheikh Hasina": "শেখ হাসিনা",
  "University of Dhaka": "ঢাকা বিশ্ববিদ্যালয়",
  "Padma Bridge": "পদ্মা সেতু"
}
```

**Mapping Sources**:
1. **Manual Dictionary**: Common entities (top 100)
2. **Wikipedia Interlanguage Links**: Automated extraction
3. **Google Translate**: Fallback for unknown entities
4. **Transliteration**: Phonetic mapping

**Mapping Strategy**:
```python
def map_entity(entity, source_lang, target_lang):
    # 1. Check dictionary first (fast, accurate)
    if entity in mapping_dict:
        return mapping_dict[entity]

    # 2. Try transliteration (for names)
    if is_proper_noun(entity):
        return transliterate(entity, source_lang, target_lang)

    # 3. Fallback to translation API
    return translate_api(entity, source_lang, target_lang)
```

**Examples**:
```python
map_entity("Bangladesh", "english", "bangla")  # → "বাংলাদেশ"
map_entity("ঢাকা", "bangla", "english")         # → "Dhaka"
map_entity("Sheikh Hasina", "english", "bangla") # → "শেখ হাসিনা"
```

---

## Phase 6: Query Processing Pipeline (Day 5-6)

### 6.1 Query Processor

**File**: `src/query_processing/query_processor.py`

**Key Components**:
```python
class QueryProcessor:
    - __init__(config)
    - process(query)                    # Main pipeline
    - detect_language(query)
    - normalize(query)
    - translate(query)
    - expand(query)
    - extract_and_map_entities(query)
    - generate_query_variants()
```

**Processing Pipeline**:
```python
def process(self, query: str) -> dict:
    """
    Full query processing pipeline

    Input: "শিক্ষা ব্যবস্থা ঢাকা"

    Output: {
        'original_query': 'শিক্ষা ব্যবস্থা ঢাকা',
        'language': 'bangla',
        'normalized': 'শিক্ষা ব্যবস্থা ঢাকা',
        'translated': 'education system Dhaka',
        'expanded_terms': {
            'শিক্ষা': ['শিক্ষা', 'education', 'বিদ্যা'],
            'ব্যবস্থা': ['ব্যবস্থা', 'system'],
            'ঢাকা': ['ঢাকা', 'Dhaka']
        },
        'entities': [
            {'text': 'ঢাকা', 'type': 'GPE', 'mapped': 'Dhaka'}
        ],
        'query_variants': [
            'শিক্ষা ব্যবস্থা ঢাকা',
            'education system Dhaka',
            'শিক্ষা system ঢাকা'  # mixed
        ]
    }
    """
    result = {}

    # Step 1: Language detection
    result['language'] = self.language_detector.detect(query)
    result['original_query'] = query

    # Step 2: Normalization
    result['normalized'] = self.normalizer.normalize(query)

    # Step 3: Translation
    if result['language'] == 'bangla':
        result['translated'] = self.translator.translate(
            result['normalized'], 'bangla', 'english'
        )
    elif result['language'] == 'english':
        result['translated'] = self.translator.translate(
            result['normalized'], 'english', 'bangla'
        )

    # Step 4: Entity extraction and mapping
    entities = self.ne_recognizer.extract_entities(result['normalized'])
    result['entities'] = []
    for entity in entities:
        mapped = self.ne_mapper.map_entity(
            entity['text'],
            result['language'],
            'english' if result['language'] == 'bangla' else 'bangla'
        )
        result['entities'].append({
            'text': entity['text'],
            'type': entity['type'],
            'mapped': mapped
        })

    # Step 5: Query expansion
    result['expanded_terms'] = self.expander.expand(result['normalized'])

    # Step 6: Generate query variants
    result['query_variants'] = self._generate_variants(result)

    return result
```

**Query Variants**:
```python
Original query: "শিক্ষা ব্যবস্থা"

Variants generated:
1. Original: "শিক্ষা ব্যবস্থা"
2. Translated: "education system"
3. Expanded (Bangla): "শিক্ষা বিদ্যা ব্যবস্থা"
4. Expanded (English): "education learning system"
5. Mixed: "শিক্ষা system" (code-switching)

These variants are sent to retrieval models
```

---

## Phase 7: Error Handling & Edge Cases (Day 6-7)

### 7.1 Error Scenarios

**1. Translation Failures**
```python
try:
    translated = translator.translate(query)
except TranslationError:
    # Fallback 1: Use cached translation if available
    # Fallback 2: Skip translation, use original query
    # Fallback 3: Use dictionary-based translation
    logger.warning(f"Translation failed for: {query}")
    translated = query  # fallback
```

**2. Empty Query**
```python
if not query or query.strip() == "":
    raise ValueError("Query cannot be empty")
```

**3. Very Long Query**
```python
MAX_QUERY_LENGTH = 500  # characters
if len(query) > MAX_QUERY_LENGTH:
    query = query[:MAX_QUERY_LENGTH]
    logger.warning("Query truncated to 500 characters")
```

**4. Unsupported Language**
```python
if language not in ['bangla', 'english', 'mixed']:
    raise ValueError(f"Unsupported language: {language}")
```

**5. No Translation Available**
```python
if translated is None:
    logger.warning(f"No translation for: {query}")
    # Use original query for same-language retrieval only
```

### 7.2 Logging

**File**: `src/utils/logger.py`

```python
import logging
import colorlog

def setup_logger(name):
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)-8s%(reset)s %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    ))

    logger = colorlog.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
```

**Usage**:
```python
logger = setup_logger('QueryProcessor')
logger.info(f"Processing query: {query}")
logger.warning(f"Translation confidence low: {confidence}")
logger.error(f"Failed to detect language: {query}")
```

---

## Integration with Retrieval Models (Module C)

### Interface for Module C

**File**: `src/query_processing/__init__.py`

```python
from .query_processor import QueryProcessor

def process_query(query: str) -> dict:
    """
    Public interface for query processing

    This function is used by retrieval models (Module C)

    Args:
        query: Raw user query (Bangla or English)

    Returns:
        dict with processed query information:
        - original_query
        - language
        - normalized
        - translated
        - expanded_terms
        - entities
        - query_variants
    """
    processor = QueryProcessor()
    return processor.process(query)
```

**Usage by Teammates (Module C)**:
```python
from src.query_processing import process_query

# User submits query
user_query = "শিক্ষা ব্যবস্থা"

# Process query
processed = process_query(user_query)

# Use processed query for retrieval
query_variants = processed['query_variants']
for variant in query_variants:
    # Retrieve documents using this variant
    results = retriever.retrieve(variant)
```

---

## Testing & Validation

### Test Cases

**File**: `tests/test_query_processing.py`

```python
import pytest
from src.query_processing import process_query

class TestQueryProcessing:

    def test_bangla_query_detection(self):
        query = "শিক্ষা ব্যবস্থা"
        result = process_query(query)
        assert result['language'] == 'bangla'

    def test_english_query_detection(self):
        query = "education system"
        result = process_query(query)
        assert result['language'] == 'english'

    def test_mixed_query_detection(self):
        query = "শিক্ষা education"
        result = process_query(query)
        assert result['language'] == 'mixed'

    def test_bangla_to_english_translation(self):
        query = "শিক্ষা"
        result = process_query(query)
        assert 'education' in result['translated'].lower()

    def test_entity_extraction(self):
        query = "ঢাকা বিশ্ববিদ্যালয়"
        result = process_query(query)
        assert len(result['entities']) > 0

    def test_query_expansion(self):
        query = "education"
        result = process_query(query)
        assert len(result['expanded_terms']) > 0

    def test_empty_query(self):
        with pytest.raises(ValueError):
            process_query("")

    def test_query_variants_generated(self):
        query = "শিক্ষা"
        result = process_query(query)
        assert len(result['query_variants']) >= 2  # at least original + translated
```

---

## Configuration

**File**: `config/query_processing_config.yaml`

```yaml
# Query Processing Configuration

language_detection:
  confidence_threshold: 0.7
  character_based: true  # Use character-based for short queries

normalization:
  lowercase: true  # for English
  unicode_normalize: true  # for Bangla
  remove_punctuation: false
  remove_stopwords: false  # optional

translation:
  service: "google_translate"  # or "huggingface", "custom"
  cache_translations: true
  fallback_to_dictionary: true
  max_retries: 3

query_expansion:
  enabled: true
  max_expansions: 3
  methods:
    - synonyms
    - transliteration
    # - morphological  # complex, may skip
  weights:
    original: 1.0
    synonym: 0.7
    transliteration: 0.8

named_entity:
  enabled: true
  extract: true
  map_to_other_language: true
  use_dictionary: true
  fallback_to_transliteration: true

logging:
  level: "INFO"
  log_file: "logs/query_processing.log"
```

---

## Deliverables

### Code Files
- [ ] `src/query_processing/__init__.py`
- [ ] `src/query_processing/query_processor.py`
- [ ] `src/query_processing/language_detector.py`
- [ ] `src/query_processing/normalizer.py`
- [ ] `src/query_processing/translator.py`
- [ ] `src/query_processing/query_expander.py`
- [ ] `src/query_processing/ne_recognizer.py`
- [ ] `src/query_processing/ne_mapper.py`

### Data Files
- [ ] `data/resources/bangla_synonyms.json`
- [ ] `data/resources/entity_mappings.json`
- [ ] `data/resources/translation_cache.json`

### Scripts
- [ ] `scripts/test_query.py`

### Tests
- [ ] `tests/test_query_processing.py`
- [ ] `tests/test_translation.py`
- [ ] `tests/test_ne_mapping.py`

### Documentation
- [ ] Query processing pipeline diagram
- [ ] Example query transformations
- [ ] Error cases and handling

---

## Success Criteria

1. ✅ **Language Detection**: >95% accuracy on test queries
2. ✅ **Translation**: Reasonable quality (manual check of 20 queries)
3. ✅ **Entity Mapping**: >80% of common entities mapped correctly
4. ✅ **Query Expansion**: Generates 2-5 relevant variants per query
5. ✅ **Error Handling**: Graceful fallbacks for all error cases
6. ✅ **Performance**: Process query in <500ms
7. ✅ **Interface**: Clean API for retrieval models

---

## Timeline Summary

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Language detection & normalization | Working detector |
| 2-3 | Translation implementation | Query translator |
| 3-4 | Query expansion | Expansion module |
| 4-5 | Named entity mapping | NE mapper |
| 5-6 | Integration & pipeline | Full pipeline |
| 6-7 | Testing & validation | Test suite |

**Total**: 7 days (Week 1-2, overlaps with Module A)

---

## Next Steps

After Module B completion:
1. Provide interface to Module C (Retrieval Models)
2. Test with real queries
3. Collect failure cases for error analysis (Module D)
4. Document translation quality issues
