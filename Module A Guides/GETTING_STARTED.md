# Getting Started with Module A

Simple guide to start using the implementation.

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
# Activate virtual environment
venv\Scripts\activate

# Install packages
pip install requests beautifulsoup4 lxml

# You can install all later:
# pip install -r requirements.txt
```

### 2. Test the Implementation

```bash
# Test all components
python scripts/test_module_a.py
```

You should see:
```
Testing Module A Components
1️⃣  Testing Text Cleaner...
  ✓ Text cleaner working
2️⃣  Testing Language Detector...
  ✓ Language detector working
...
✅ All tests passed!
```

## Start Crawling (Test Mode)

### Option 1: Small Test (Recommended First)

```bash
# Collect just 10 documents per site for testing
python scripts/run_crawler.py --test --language english
```

This will:
- Crawl 5 English news sites
- Collect 10 documents from each
- Save to `data/processed/english_docs.json`
- Take about 2-3 minutes

### Option 2: Full Crawl (Production)

```bash
# Collect 2,500 documents per language
python scripts/run_crawler.py --language both --target 2500
```

This will:
- Crawl 5 Bangla + 5 English sites
- Collect ~500 documents from each site
- Take 2-3 hours (with 2-second delays)

### Option 3: One Language Only

```bash
# Just Bangla
python scripts/run_crawler.py --language bangla --target 2500

# Just English
python scripts/run_crawler.py --language english --target 2500
```

## Build Index

After crawling:

```bash
# Build inverted index
python scripts/build_index.py
```

This creates:
- `data/indices/bangla_index.pkl`
- `data/indices/english_index.pkl`

## Verify Data Quality

```bash
# Check collected data
python scripts/verify_data.py
```

Shows:
- Document counts
- Language detection accuracy
- Missing fields
- Statistics

## File Structure

After running everything:

```
data/
├── processed/
│   ├── bangla_docs.json       # Bangla documents
│   ├── bangla_metadata.csv    # Bangla metadata
│   ├── english_docs.json      # English documents
│   └── english_metadata.csv   # English metadata
└── indices/
    ├── bangla_index.pkl       # Bangla inverted index
    └── english_index.pkl      # English inverted index
```

## Common Issues

### Issue: "ModuleNotFoundError"
**Solution**: Make sure you're in the project directory and virtual environment is activated.

### Issue: "Connection timeout"
**Solution**: Some sites may be slow. The crawler will retry automatically.

### Issue: "Not enough documents collected"
**Solution**:
- Check internet connection
- Try different sites
- Increase timeout in config

### Issue: Crawling is too slow
**Solution**: Reduce delay in `scripts/run_crawler.py`:
```python
'delay_between_requests': 1,  # Faster but less respectful
```

## What's Next?

After Module A is complete:

1. **Module B**: Implement query processing
   - Language detection for queries
   - Query translation
   - Query expansion

2. **Integration**: Your teammates will use your indices
   - They'll implement retrieval models (BM25, semantic)
   - They'll use your DocumentStore and InvertedIndex classes

3. **Testing**: Create test queries
   - Sample Bangla queries
   - Sample English queries
   - Test cross-lingual retrieval

## Need Help?

Check these files:
- Full implementation plan: `docs/module_a_implementation_plan.md`
- Code documentation: Docstrings in each file
- Example usage: `scripts/test_module_a.py`

## Quick Commands Reference

```bash
# Test implementation
python scripts/test_module_a.py

# Test crawl (10 docs per site)
python scripts/run_crawler.py --test --language english

# Full crawl (both languages)
python scripts/run_crawler.py --language both --target 2500

# Build indices
python scripts/build_index.py

# Verify data
python scripts/verify_data.py
```

Good luck! 🚀
