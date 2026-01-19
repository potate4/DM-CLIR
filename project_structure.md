# CLIR Project Structure

```
DM-CLIR/
├── README.md                          # Project overview and setup instructions
├── requirements.txt                   # Python dependencies
├── .gitignore                        # Git ignore file
├── .env.example                      # Environment variables template
│
├── config/                           # Configuration files
│   ├── crawler_config.yaml          # Crawler settings (sites, delays, etc.)
│   ├── indexer_config.yaml          # Indexing configuration
│   ├── model_config.yaml            # Model parameters
│   └── sites.json                   # News sites list (Bangla & English)
│
├── data/                             # Data directory (add to .gitignore)
│   ├── raw/                         # Raw crawled data
│   │   ├── bangla/                  # Bangla news articles
│   │   └── english/                 # English news articles
│   ├── processed/                   # Processed documents
│   │   ├── documents.json           # All documents with metadata
│   │   ├── bangla_docs.json        # Bangla documents only
│   │   ├── english_docs.json       # English documents only
│   │   └── metadata.csv            # Document metadata table
│   ├── indices/                     # Index files
│   │   ├── inverted_index.pkl      # Inverted index
│   │   └── embeddings/             # Document embeddings
│   └── evaluation/                  # Evaluation data
│       ├── labeled_queries.csv      # Manually labeled queries
│       └── results/                 # Evaluation results
│
├── src/                              # Source code
│   ├── __init__.py
│   │
│   ├── crawler/                      # MODULE A: Data Collection
│   │   ├── __init__.py
│   │   ├── base_crawler.py          # Base crawler class
│   │   ├── news_crawler.py          # News site crawler implementation
│   │   ├── rss_crawler.py           # RSS feed crawler (fallback)
│   │   └── utils.py                 # Crawler utilities
│   │
│   ├── preprocessing/                # MODULE A: Data Preprocessing
│   │   ├── __init__.py
│   │   ├── text_cleaner.py          # Text cleaning and normalization
│   │   ├── language_detector.py     # Language detection
│   │   ├── tokenizer.py             # Tokenization (Bangla & English)
│   │   └── metadata_extractor.py    # Extract title, date, etc.
│   │
│   ├── indexing/                     # MODULE A: Indexing
│   │   ├── __init__.py
│   │   ├── inverted_index.py        # Inverted index implementation
│   │   ├── document_store.py        # Document storage and retrieval
│   │   └── embeddings_store.py      # Store and manage embeddings
│   │
│   ├── query_processing/             # MODULE B: Query Processing
│   │   ├── __init__.py
│   │   ├── query_processor.py       # Main query processing pipeline
│   │   ├── normalizer.py            # Query normalization
│   │   ├── translator.py            # Query translation (Bangla ↔ English)
│   │   ├── query_expander.py        # Query expansion (synonyms, etc.)
│   │   └── ne_mapper.py             # Named entity mapping
│   │
│   ├── retrieval/                    # MODULE C: Retrieval Models (Teammates)
│   │   ├── __init__.py
│   │   ├── base_retriever.py        # Base retriever interface
│   │   ├── bm25_retriever.py        # BM25 implementation
│   │   ├── tfidf_retriever.py       # TF-IDF implementation
│   │   ├── fuzzy_retriever.py       # Fuzzy/transliteration matching
│   │   ├── semantic_retriever.py    # Semantic embedding-based retrieval
│   │   └── hybrid_retriever.py      # Hybrid ranking (optional)
│   │
│   ├── ranking/                      # MODULE D: Ranking & Scoring (Teammates)
│   │   ├── __init__.py
│   │   ├── ranker.py                # Ranking function
│   │   └── scorer.py                # Confidence scoring
│   │
│   ├── evaluation/                   # MODULE D: Evaluation (Teammates)
│   │   ├── __init__.py
│   │   ├── metrics.py               # Precision@10, Recall@50, nDCG, MRR
│   │   ├── evaluator.py             # Evaluation runner
│   │   └── error_analyzer.py        # Error analysis tools
│   │
│   └── utils/                        # Shared utilities
│       ├── __init__.py
│       ├── logger.py                # Logging configuration
│       ├── timer.py                 # Performance timing
│       └── helpers.py               # Common helper functions
│
├── notebooks/                        # Jupyter notebooks for exploration
│   ├── 01_data_exploration.ipynb    # Explore crawled data
│   ├── 02_indexing_test.ipynb       # Test indexing
│   ├── 03_query_processing.ipynb    # Test query processing
│   ├── 04_model_comparison.ipynb    # Compare retrieval models
│   └── 05_error_analysis.ipynb      # Error analysis
│
├── scripts/                          # Executable scripts
│   ├── run_crawler.py               # Run the crawler
│   ├── build_index.py               # Build indices
│   ├── test_query.py                # Test query processing
│   ├── search_cli.py                # CLI search interface
│   └── evaluate.py                  # Run evaluation
│
├── tests/                            # Unit tests
│   ├── __init__.py
│   ├── test_crawler.py
│   ├── test_indexing.py
│   ├── test_query_processing.py
│   └── test_retrieval.py
│
└── docs/                             # Documentation
    ├── ai_usage_log.md              # AI tool usage log (required)
    ├── literature_review.md         # Literature review notes
    └── error_cases.md               # Documented error cases
```

## Module Ownership

### Your Modules (Module A & B):
- `src/crawler/` - Web crawling
- `src/preprocessing/` - Text preprocessing
- `src/indexing/` - Index construction
- `src/query_processing/` - Query processing pipeline

### Teammates' Modules (Module C, D, E):
- `src/retrieval/` - Retrieval models
- `src/ranking/` - Ranking and scoring
- `src/evaluation/` - Evaluation metrics and analysis
- `docs/` - Report and literature review

### Shared:
- `src/utils/` - Common utilities
- `config/` - Configuration files
- `data/` - Data storage
