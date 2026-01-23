"""
Run web crawler to collect news articles.

Uses advanced crawling strategies:
- API-based (Prothom Alo)
- Sitemap-based (Daily Star)
- Cloudscraper (Kaler Kantho, etc.)
- RSS feeds (fallback)
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.crawler.advanced_crawler import AdvancedCrawler
from src.preprocessing.text_cleaner import TextCleaner
from src.indexing.document_store import DocumentStore
from src.utils.logger import setup_logger


def crawl_bangla(target: int, logger) -> DocumentStore:
    """Crawl Bangla news sources"""
    logger.info(f"\n{'='*60}")
    logger.info("Crawling BANGLA sources")
    logger.info(f"Target: {target} documents")
    logger.info(f"{'='*60}\n")

    crawler = AdvancedCrawler(language='bangla', delay=0.5)
    cleaner = TextCleaner('bangla')
    doc_store = DocumentStore()

    # Calculate per-source limits
    per_source = target

    # 1. Prothom Alo (API - most reliable, unlimited articles)
    logger.info("\n[1/4] Crawling Prothom Alo (API)...")
    crawler.crawl_prothom_alo_api(limit=per_source)

    # # 2. Kaler Kantho (cloudscraper)
    # logger.info("\n[2/4] Crawling Kaler Kantho (cloudscraper)...")
    # crawler.crawl_kaler_kantho(limit=per_source)

    # # 3. RSS feeds for remaining sources
    # remaining = target - crawler.get_count()
    # if remaining > 0:
    #     logger.info(f"\n[3/4] Crawling RSS feeds (need {remaining} more)...")

    #     rss_sources = [
    #         ("https://www.banglatribune.com/rss.xml", "Bangla Tribune"),
    #         ("https://www.prothomalo.com/feed/", "Prothom Alo RSS"),
    #     ]

    #     per_rss = remaining // len(rss_sources)
    #     for feed_url, name in rss_sources:
    #         if crawler.get_count() >= target:
    #             break
    #         crawler.crawl_rss_feed(feed_url, name, per_rss)

    # Process and store documents
    logger.info(f"\nProcessing {crawler.get_count()} collected documents...")

    for doc in crawler.get_documents():
        doc['title'] = cleaner.clean(doc['title'])
        doc['body'] = cleaner.clean(doc['body'])
        doc_store.add_document(doc)

    return doc_store


def crawl_english(target: int, logger) -> DocumentStore:
    """Crawl English news sources"""
    logger.info(f"\n{'='*60}")
    logger.info("Crawling ENGLISH sources")
    logger.info(f"Target: {target} documents")
    logger.info(f"{'='*60}\n")

    crawler = AdvancedCrawler(language='english', delay=0.5)
    cleaner = TextCleaner('english')
    doc_store = DocumentStore()

    logger.info("\n[1/1] Crawling English sources (multi-strategy)...")
    crawler.crawl_english(total_limit=target)

    # Process and store documents
    logger.info(f"\nProcessing {crawler.get_count()} collected documents...")

    for doc in crawler.get_documents():
        doc['title'] = cleaner.clean(doc['title'])
        doc['body'] = cleaner.clean(doc['body'])
        doc_store.add_document(doc)

    return doc_store


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Crawl news websites using advanced strategies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Crawling strategies:
  - Prothom Alo: Uses official API (1.3M+ articles available)
  - Daily Star: Uses sitemap (paginated XML)
  - Kaler Kantho: Uses cloudscraper (Cloudflare bypass)
  - Others: RSS feeds and archive pages

Examples:
  python run_crawler.py --language bangla --target 2500
  python run_crawler.py --language english --target 2500
  python run_crawler.py --language both --target 5000
  python run_crawler.py --test  # Quick test with 50 docs
        """
    )

    parser.add_argument(
        '--language',
        choices=['bangla', 'english', 'both'],
        default='both',
        help='Language to crawl'
    )
    parser.add_argument(
        '--target',
        type=int,
        default=2500,
        help='Target documents per language (default: 2500)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode (50 docs per language)'
    )

    args = parser.parse_args()

    logger = setup_logger('Crawler')

    # Test mode
    if args.test:
        args.target = 50
        print("\n[TEST MODE] Collecting 50 documents per language\n")

    # Determine languages
    if args.language == 'both':
        languages = ['bangla', 'english']
    else:
        languages = [args.language]

    # Output directory
    output_dir = Path(__file__).parent.parent / 'data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Crawl each language
    for language in languages:
        if language == 'bangla':
            doc_store = crawl_bangla(args.target, logger)
        else:
            doc_store = crawl_english(args.target, logger)

        # Save documents
        output_file = output_dir / f"{language}_docs.json"
        doc_store.save(output_file)

        # Save metadata CSV
        metadata_file = output_dir / f"{language}_metadata.csv"
        doc_store.save_metadata_csv(metadata_file)

        # Print statistics
        stats = doc_store.get_statistics()
        print(f"\n{'='*60}")
        print(f"{language.upper()} CRAWL COMPLETE")
        print(f"{'='*60}")
        
        if stats:
            print(f"Total documents: {stats.get('total_documents', 0)}")
            print(f"Average words: {stats.get('average_word_count', 0):.0f}")
            print(f"\nBy source:")
            for source, count in stats.get('by_source', {}).items():
                print(f"  {source}: {count}")
            print(f"\nBy method:")
            methods = {}
            for doc in doc_store.documents.values():
                method = doc.get('method', 'unknown')
                methods[method] = methods.get(method, 0) + 1
            for method, count in methods.items():
                print(f"  {method}: {count}")
        else:
            print("No documents collected")
        
        print(f"\nSaved to: {output_file}")
        print(f"{'='*60}\n")

    print("[DONE] Crawling complete!")


if __name__ == '__main__':
    main()
