# Query Processing Guide

Detailed guide for the cross-lingual query processing pipeline.

## Overview

Module B handles the critical task of processing user queries for cross-lingual information retrieval. The pipeline ensures that:

1. Queries in any language (Bangla or English) can find documents in both languages
2. Named entities are correctly mapped across languages
3. Query expansion improves recall with synonyms

## Pipeline Stages

### Stage 1: Language Detection

**Purpose**: Determine if query is Bangla, English, or mixed.

**How it works**:
- Counts Bangla characters (Unicode U+0980 to U+09FF)
- Counts English characters (a-z, A-Z)
- Compares ratios to classify

**Example**:
```python
"education system"     -> english (100% English chars)
"শিক্ষা ব্যবস্থা"           -> bangla (100% Bangla chars)
"dhaka শহর"            -> mixed (both present)
```

### Stage 2: Normalization

**Purpose**: Clean and standardize query text.

**Steps**:
1. Strip leading/trailing whitespace
2. Collapse multiple spaces to single space
3. Convert to lowercase (English)
4. Apply Unicode NFC normalization (Bangla)
5. Optionally remove stopwords

**Example**:
```
Input:  "  EDUCATION   System  "
Output: "education system"
```

### Stage 3: Translation

**Purpose**: Translate query to the other language for cross-lingual search.

**Methods**:
1. **Dictionary Lookup** (default, offline)
   - 30+ common terms pre-mapped
   - Fast and reliable
   - Limited vocabulary

2. **Google Translate API** (optional)
   - Requires `deep_translator` package
   - Better quality
   - Needs internet

**Example**:
```
"education" (English) -> "শিক্ষা" (Bangla)
"রাজনীতি" (Bangla)    -> "politics" (English)
```

### Stage 4: Named Entity Mapping

**Purpose**: Map named entities (people, places, organizations) across languages.

**Categories covered**:
- Countries: bangladesh, india, pakistan, etc.
- Cities: dhaka, chittagong, sylhet, etc.
- People: sheikh hasina, shakib al hasan, etc.
- Organizations: dhaka university, grameen bank, etc.
- Landmarks: padma bridge, sundarbans, etc.

**Example**:
```
"dhaka university cricket"
-> Entities found: dhaka (ঢাকা), university (mapped as part of 'dhaka university')
```

### Stage 5: Query Expansion

**Purpose**: Add synonyms to improve recall.

**Coverage**:
- Education terms
- Political terms
- Sports terms
- Business terms
- Health terms
- And more...

**Example**:
```
"education" -> ["education", "learning", "schooling", "teaching"]
"sports"    -> ["sports", "games", "athletics", "sport"]
```

### Stage 6: Variant Generation

**Purpose**: Create all query forms for comprehensive retrieval.

**Variants include**:
1. Original normalized query
2. Translated query
3. Entity-mapped terms
4. Expanded synonyms

**Example**:
```
Query: "education in bangladesh"

Variants:
- "education in bangladesh"
- "শিক্ষা in বাংলাদেশ"
- "বাংলাদেশ"
- "learning"
- "schooling"
- "teaching"
- ... (13 total)
```

## Cross-Lingual Retrieval Strategy

### For English Query

```
User: "dhaka university news"
           |
           v
[Detect: English]
           |
           v
[Translate to Bangla: "ঢাকা বিশ্ববিদ্যালয় সংবাদ"]
           |
           v
[Map entities: dhaka -> ঢাকা]
           |
           v
[Expand: news -> report, article, story]
           |
           v
Search both English AND Bangla indices
```

### For Bangla Query

```
User: "ক্রিকেট খেলা"
           |
           v
[Detect: Bangla]
           |
           v
[Translate to English: "cricket game"]
           |
           v
[Expand: cricket -> match, game, test]
           |
           v
Search both Bangla AND English indices
```

## Customization

### Add Translation Terms

```python
translator = QueryTranslator()
translator.add_translation('robotics', 'রোবটিক্স', 'english')
```

### Add Entity Mappings

```python
mapper = EntityMapper()
mapper.add_mapping('uttara', 'উত্তরা')  # Add a new place
```

### Add Synonyms

```python
expander = QueryExpander()
expander.add_synonym('startup', ['company', 'venture', 'business'], 'english')
```

## Best Practices

### 1. Always Use Full Pipeline

```python
# Good: Use full processor
processor = QueryProcessor()
result = processor.process(query)
search_terms = result['variants']

# Avoid: Using individual components separately for search
# (unless you have a specific reason)
```

### 2. Search All Variants

```python
# Good: Search with all variants
for variant in result['variants']:
    results.extend(search(variant))

# Bad: Only search original query
results = search(query)  # Misses cross-lingual results
```

### 3. Handle Mixed Language

```python
result = processor.process(query)
if result['language'] == 'mixed':
    # Query has both Bangla and English
    # All variants already handle this
    pass
```

## Troubleshooting

### Translation Warning

```
WARNING - deep_translator not installed. Using fallback dictionary.
```

**Solution**: This is fine for basic use. For better translation:
```bash
pip install deep-translator
```

### Encoding Issues (Windows)

If you see encoding errors with Bangla text:
- The code handles this internally
- Log messages show character counts instead of actual Bangla text
- All processing works correctly

### Unknown Terms

If a term isn't translated/expanded:
- Add it to the dictionaries
- Or rely on the original term for exact matching

## Performance Tips

1. **Reuse processor**: Create once, use many times
   ```python
   processor = QueryProcessor()  # Create once
   for query in queries:
       result = processor.process(query)  # Reuse
   ```

2. **Disable expansion if not needed**:
   ```python
   processor = QueryProcessor(expand_queries=False)
   ```

3. **Cache results**: For repeated queries, cache the processed result

## Integration Example

```python
from src.query_processing import QueryProcessor
from src.indexing.inverted_index import InvertedIndex

# Initialize
processor = QueryProcessor()
en_index = InvertedIndex('english')
bn_index = InvertedIndex('bangla')

en_index.load('data/indices/english_index.pkl')
bn_index.load('data/indices/bangla_index.pkl')

def cross_lingual_search(query):
    """Search both languages"""
    result = processor.process(query)

    all_docs = set()

    for variant in result['variants']:
        words = variant.split()
        for word in words:
            # Search English index
            postings = en_index.get_postings(word)
            all_docs.update(postings.keys())

            # Search Bangla index
            postings = bn_index.get_postings(word)
            all_docs.update(postings.keys())

    return list(all_docs)
```
