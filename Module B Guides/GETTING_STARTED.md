# Getting Started with Module B

Quick guide to using the Query Processing module.

## Quick Test

```bash
# Run all Module B tests
python scripts/test_module_b.py
```

## Basic Usage

### Process a Query

```python
from src.query_processing import QueryProcessor

processor = QueryProcessor()
result = processor.process("education in bangladesh")

print(result['language'])      # 'english'
print(result['normalized'])    # 'education in bangladesh'
print(result['variants'])      # List of all query variants
```

### One-Liner

```python
from src.query_processing import process_query

result = process_query("dhaka university")
```

## Individual Components

### 1. Detect Language

```python
from src.query_processing import QueryLanguageDetector

detector = QueryLanguageDetector()
lang = detector.detect("cricket match")  # 'english'
```

### 2. Normalize Query

```python
from src.query_processing import QueryNormalizer

normalizer = QueryNormalizer()
clean = normalizer.normalize("  CRICKET  Match  ", 'english')  # 'cricket match'
```

### 3. Translate Query

```python
from src.query_processing import QueryTranslator

translator = QueryTranslator()
translated = translator.translate("education", 'english', 'bangla')
```

### 4. Expand Query

```python
from src.query_processing import QueryExpander

expander = QueryExpander()
expanded = expander.expand("education", 'english')
# {'education': ['education', 'learning', 'schooling', 'teaching']}
```

### 5. Map Entities

```python
from src.query_processing import EntityMapper

mapper = EntityMapper()
mapped = mapper.map_entity("dhaka", 'english', 'bangla')
```

## Result Structure

```python
result = processor.process("education in bangladesh")

# result contains:
{
    'original': 'education in bangladesh',
    'language': 'english',
    'normalized': 'education in bangladesh',
    'translated': '...',  # Bangla translation
    'expanded': {
        'education': ['education', 'learning', ...],
        'bangladesh': ['bangladesh']
    },
    'entities': [
        {'original': 'bangladesh', 'mapped': '...', ...}
    ],
    'variants': [
        'education in bangladesh',
        '...',  # translated version
        'learning',  # expanded terms
        ...
    ]
}
```

## For Retrieval (Module C)

```python
processor = QueryProcessor()
result = processor.process(user_query)

# Use all variants for comprehensive search
for query_variant in result['variants']:
    # Search with each variant
    search(query_variant)
```

## Optional: Better Translation

Install for Google Translate API support:

```bash
pip install deep-translator
```

Without this, dictionary-based translation is used (works offline).

## Common Tasks

### Get Search Terms

```python
result = processor.process("education system")
terms = result['normalized'].split()  # ['education', 'system']
```

### Get All Query Variants

```python
result = processor.process("dhaka university")
all_queries = result['variants']  # Use all for cross-lingual search
```

### Check If Entity Was Found

```python
result = processor.process("dhaka cricket match")
if result['entities']:
    print(f"Found {len(result['entities'])} entities")
```

## Files

```
src/query_processing/
├── language_detector.py   # Language detection
├── normalizer.py          # Query cleaning
├── translator.py          # Translation
├── expander.py            # Synonym expansion
├── entity_mapper.py       # Named entity mapping
└── query_processor.py     # Main pipeline
```

## Next Steps

1. Integrate with Module A indices for search
2. Pass results to Module C for retrieval
3. Use language info in Module D for reranking
