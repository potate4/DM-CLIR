# Cross-Lingual Information Retrieval (CLIR) System

A multilingual information retrieval engine for Bangla and English documents, implementing lexical, fuzzy, and semantic retrieval methods.

## Course Information
- **Course**: Data Mining - CSE 4739
- **Project**: Cross-Lingual Information Retrieval System
- **Timeline**: 3 weeks
- **Team Size**: 4 members

## Project Overview

This system enables users to search for documents in one language (Bangla or English) and retrieve relevant results in both languages. It combines multiple retrieval techniques:

- **Lexical Retrieval**: TF-IDF and BM25
- **Fuzzy Matching**: Transliteration and edit distance
- **Semantic Retrieval**: Multilingual embeddings (LaBSE, XLM-R)
- **Hybrid Ranking**: Combined scoring from multiple models

## Features

- Web crawling from 10+ Bangla and English news sites
- Multilingual indexing with inverted index
- Cross-lingual query processing with translation
- Named entity mapping across languages
- Multiple retrieval models with comparison
- Comprehensive evaluation metrics (Precision@10, Recall@50, nDCG, MRR)
- Error analysis and visualization

## Project Structure

```
DM-CLIR/
├── config/              # Configuration files
├── data/               # Data storage (raw, processed, indices)
├── src/                # Source code
│   ├── crawler/        # Module A: Web crawling
│   ├── preprocessing/  # Module A: Text preprocessing
│   ├── indexing/       # Module A: Index construction
│   ├── query_processing/ # Module B: Query processing
│   ├── retrieval/      # Module C: Retrieval models
│   ├── ranking/        # Module D: Ranking
│   └── evaluation/     # Module D: Evaluation
├── notebooks/          # Jupyter notebooks
├── scripts/            # Executable scripts
└── docs/              # Documentation
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd DM-CLIR
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download NLP Models

```bash
# Download spaCy models
python -m spacy download en_core_web_sm
python -m spacy download xx_ent_wiki_sm  # multilingual

# Download NLTK data
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"
```

### 5. Configure Environment

Create a `.env` file in the root directory (optional):

```
# Add any API keys or sensitive configuration
# TRANSLATION_API_KEY=your_key_here
```

## Usage

### Step 1: Crawl Data

```bash
python scripts/run_crawler.py --language both --target 2500
```

This will crawl 2,500 documents from each language (Bangla and English).

### Step 2: Build Index

```bash
python scripts/build_index.py
```

This creates the inverted index and generates document embeddings.

### Step 3: Search

```bash
# CLI search
python scripts/search_cli.py

# Or test a single query
python scripts/test_query.py --query "শিক্ষা" --top-k 10
```

### Step 4: Evaluate

```bash
python scripts/evaluate.py --queries data/evaluation/labeled_queries.csv
```

## Module Breakdown

### Module A: Dataset Construction & Indexing (12 + 8 = 20%)
**Owners**: Your Team

- Web crawling from 5 Bangla + 5 English news sites
- Metadata extraction (title, body, url, date, language)
- Text preprocessing and normalization
- Inverted index construction
- Optional: Named entity extraction, embeddings

**Files**: `src/crawler/`, `src/preprocessing/`, `src/indexing/`

### Module B: Query Processing & Cross-Lingual Handling (15%)
**Owners**: Your Team

- Language detection
- Query normalization
- Query translation (Bangla ↔ English)
- Query expansion with synonyms
- Named entity mapping

**Files**: `src/query_processing/`

### Module C: Retrieval Models (18%)
**Owners**: Teammates

- BM25 retrieval
- TF-IDF retrieval
- Fuzzy/transliteration matching
- Semantic retrieval with embeddings
- Optional: Hybrid ranking

**Files**: `src/retrieval/`

### Module D: Ranking, Scoring & Evaluation (15 + 10 = 25%)
**Owners**: Teammates

- Ranking function with confidence scores
- Evaluation metrics (Precision@10, Recall@50, nDCG, MRR)
- Query execution time measurement
- Error analysis

**Files**: `src/ranking/`, `src/evaluation/`

### Module E: Report, Literature Review & Innovation (15 + 7 = 22%)
**Owners**: All Team Members

- Literature review (3-5 papers)
- Methodology documentation
- Results and analysis
- AI usage log
- Innovation proposal

**Files**: `docs/`

## Dataset

### Target
- Minimum 2,500 documents per language
- Total: 5,000+ documents

### Sources

**Bangla Sites**:
1. Prothom Alo (prothomalo.com)
2. BD News 24 (bangla.bdnews24.com)
3. Kaler Kantho (kalerkantho.com)
4. Bangla Tribune (banglatribune.com)
5. Dhaka Post (dhakapost.com)

**English Sites**:
1. The Daily Star (thedailystar.net)
2. New Age (newagebd.net)
3. The New Nation (dailynewnation.com)
4. Daily Sun (daily-sun.com)
5. Dhaka Tribune (dhakatribune.com)

## Evaluation Metrics

- **Precision@10**: At least 6 relevant in top 10 (≥0.6)
- **Recall@50**: At least 50% of relevant docs retrieved (≥0.5)
- **nDCG@10**: ≥0.5
- **MRR**: ≥0.4

## Technologies

- **Language**: Python 3.8+
- **Crawling**: BeautifulSoup, Selenium, Requests
- **NLP**: spaCy, NLTK, HuggingFace Transformers
- **Embeddings**: LaBSE, XLM-R, sentence-transformers
- **Translation**: Deep Translator, Google Translate API
- **Indexing**: Custom inverted index / Whoosh
- **Evaluation**: scikit-learn, custom metrics

## Team Collaboration

### Git Workflow
1. Create feature branches for your module
2. Make small, frequent commits
3. Write clear commit messages
4. Create pull requests for review
5. Never commit large data files (use .gitignore)

### Communication
- Weekly sync meetings
- Share progress updates
- Document any blockers
- Review each other's code

## AI Usage Policy

All AI tool usage must be documented in `docs/ai_usage_log.md` with:
- Exact prompts used
- Tool name and version
- Generated output
- Verification notes
- Corrections made (if any)

## Timeline

- **Week 1**: Dataset crawling & indexing (Module A)
- **Week 1-2**: Query processing & retrieval models (Modules B & C)
- **Week 2-3**: Evaluation & error analysis (Module D)
- **Week 3**: Report writing & polish (Module E)

## License

Academic project for CSE 4739 - Data Mining

## Contributors

- [Your Name] - Modules A & B
- [Teammate 1] - Module C
- [Teammate 2] - Module D
- [Teammate 3] - Module E

## References

See `docs/literature_review.md` for detailed paper summaries.