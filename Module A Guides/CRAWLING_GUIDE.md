# Crawling Guide - What Works & What Doesn't

## Current Status

The crawler implementation is **working** but some sites are blocking requests or have issues:

### Working Sites
- **The Daily Star** ✓ - HTML crawling works perfectly
- RSS feeds aren't working for most sites (need valid feed URLs)

### Blocked/Not Working
- **Daily Sun** - Returns 403 Forbidden (blocking bots)
- **New Age** - CSS selectors don't match site structure
- **The New Nation** - CSS selectors don't match
- **Dhaka Tribune** - RSS feed URL invalid

## Solution Options

### Option 1: Focus on Working Sites (Easiest)

Since only The Daily Star works reliably, you can:

1. **Crawl more from The Daily Star** (it works!)
   ```bash
   # Modify sites.json to only use The Daily Star
   # Or run multiple times with different sections/categories
   ```

2. **Find alternative Bangladeshi news sites** that don't block crawlers
   - Try sites with open APIs
   - Look for sites with valid RSS feeds

3. **Use multiple working sources** instead of exactly 5
   - The assignment says "at least" 2,500 docs
   - Quality > strict site count

### Option 2: Use Common Crawl (Advanced, Recommended)

The assignment mentions "Use Common Crawl / CC-MAIN extraction" as an advanced option.

**Common Crawl Benefits:**
- Already crawled data (no blocking issues)
- Huge dataset
- Bangla and English news available
- No rate limiting

**How to use Common Crawl:**

1. Install CC extractor:
   ```bash
   pip install warcio cdx-toolkit
   ```

2. Search for Bangladeshi news sites:
   ```python
   # Example: Extract from Common Crawl
   from cdx_toolkit import CDXFetcher

   cdx = CDXFetcher(source='cc')
   url = 'https://www.thedailystar.net/*'

   for obj in cdx.iter(url, limit=2500):
       # Process WARC records
       pass
   ```

3. Benefits:
   - No blocking
   - Historical data
   - Already archived

### Option 3: Use Pre-existing Datasets (Fastest)

Use existing Bangla-English news datasets:

1. **IndicCorp** - Large corpus of Indian languages including Bangla
2. **CC-100** - Common Crawl monolingual datasets
3. **OSCAR** - Open Super-large Crawled Aggregated coRpus
4. **BanglaBERT datasets** - Bangla news collections

Download and process these instead of crawling.

### Option 4: Fix RSS Feeds (Moderate Effort)

Update `config/sites.json` with correct RSS feed URLs:

```bash
# Test RSS feeds manually first
curl https://www.site.com/rss.xml
curl https://www.site.com/feed
```

Common RSS URL patterns:
- `/rss.xml`
- `/feed`
- `/rss`
- `/feed/rss`

## Recommended Approach

Given your situation, I recommend:

**Short term (to get started):**
1. Use The Daily Star extensively (it works!)
2. Find 2-3 more working Bangladeshi news sites
3. Or use pre-existing datasets

**Better long-term:**
- Implement Common Crawl extraction
- More reliable
- Larger dataset
- No blocking issues

## Quick Fix for Assignment

To meet the 2,500 docs requirement quickly:

```python
# Create a simple script using existing datasets
# Or download from Kaggle/HuggingFace:

from datasets import load_dataset

# Example: Load existing Bangla news
dataset = load_dataset("csebuetnlp/xlsum", "bengali")
# Process and convert to your format
```

## Current Implementation Status

What's implemented and working:
- ✓ HTML crawler with retry logic
- ✓ RSS crawler as fallback
- ✓ Text cleaning
- ✓ Language detection
- ✓ Document storage
- ✓ Inverted indexing

What needs adjustment:
- CSS selectors for specific sites
- Valid RSS feed URLs
- Anti-blocking strategies

## Next Steps

1. **Test what you have:**
   ```bash
   python scripts/run_crawler.py --test --language english
   ```

2. **Check collected data:**
   ```bash
   python scripts/verify_data.py
   ```

3. **Decide on approach:**
   - Stick with working sites + datasets?
   - Implement Common Crawl?
   - Find better RSS feeds?

4. **Continue with Module B** while data collection runs

## Assignment Compliance

The assignment says:
> "Crawling can be error-prone. If crawling fails for a site, use RSS feeds or the site's search API if available."
> "Optional and Advanced: Use Common Crawl / CC-MAIN extraction"

So using alternative methods is **explicitly allowed**!

## Need Help?

Check:
- `docs/module_a_implementation_plan.md` - Full implementation details
- `README.md` - Project overview
- Online: Common Crawl documentation, existing dataset repos

---

**Bottom Line:** The crawler works! But real-world crawling is messy. Using existing datasets or Common Crawl is perfectly valid and often better for academic projects.
