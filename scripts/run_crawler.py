"""Run web crawler to collect news articles"""

import sys
import json
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.crawler.news_crawler import NewsCrawler
from src.crawler.rss_crawler import RSSCrawler
from src.preprocessing.text_cleaner import TextCleaner
from src.preprocessing.language_detector import LanguageDetector
from src.indexing.document_store import DocumentStore
from src.utils.logger import setup_logger


def load_config():
    """Load crawler configuration"""
    config = {
        'crawler': {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'delay_between_requests': 2,
            'timeout': 30,
            'max_retries': 3
        }
    }
    return config


def load_sites():
    """Load sites configuration"""
    sites_file = Path(__file__).parent.parent / 'config' / 'sites.json'

    with open(sites_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def crawl_language(language, sites, target_per_site, config):
    """
    Crawl sites for a specific language

    Args:
        language: 'bangla' or 'english'
        sites: List of site configurations
        target_per_site: Target documents per site
        config: Crawler configuration

    Returns:
        DocumentStore with collected documents
    """
    logger = setup_logger(f'Main-{language}')
    logger.info(f"\n{'='*60}")
    logger.info(f"Crawling {language.upper()} documents")
    logger.info(f"Target: {target_per_site} docs per site, {len(sites)} sites")
    logger.info(f"{'='*60}\n")

    # Initialize components
    html_crawler = NewsCrawler(config['crawler'], language)
    rss_crawler = RSSCrawler(config['crawler'], language)
    cleaner = TextCleaner(language)
    detector = LanguageDetector()
    doc_store = DocumentStore()

    # Crawl each site
    for i, site in enumerate(sites, 1):
        logger.info(f"\n[{i}/{len(sites)}] Crawling: {site['name']}")
        logger.info(f"URL: {site['url']}")

        try:
            # Try HTML crawling first
            before_count = html_crawler.get_count()
            html_crawler.crawl_site(site, target_per_site)
            collected = html_crawler.get_count() - before_count

            # If HTML crawling got few/no documents, try RSS
            if collected < target_per_site * 0.5 and site.get('rss_feed'):
                logger.info(f"HTML crawling got {collected} docs, trying RSS feed...")
                before_rss = rss_crawler.get_count()
                rss_crawler.crawl_feed(site['rss_feed'], site['name'], target_per_site)
                rss_collected = rss_crawler.get_count() - before_rss
                logger.info(f"RSS feed collected {rss_collected} additional docs")

        except Exception as e:
            logger.error(f"Error crawling {site['name']}: {str(e)}")
            # Try RSS as fallback
            if site.get('rss_feed'):
                logger.info("Trying RSS feed as fallback...")
                try:
                    rss_crawler.crawl_feed(site['rss_feed'], site['name'], target_per_site)
                except Exception as rss_error:
                    logger.error(f"RSS also failed: {str(rss_error)}")
            continue

    # Combine documents from both crawlers
    documents = html_crawler.get_documents() + rss_crawler.get_documents()
    logger.info(f"\nProcessing {len(documents)} collected documents...")

    processed_count = 0
    for doc in documents:
        # Clean text
        doc['title'] = cleaner.clean(doc['title'])
        doc['body'] = cleaner.clean(doc['body'])

        # Verify language
        detected_lang = detector.detect(doc['body'])
        if detected_lang == language or detected_lang == 'mixed':
            doc_store.add_document(doc)
            processed_count += 1
        else:
            logger.warning(f"Language mismatch for {doc['doc_id']}: {detected_lang}")

    logger.info(f"Processed {processed_count} valid documents")

    return doc_store


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Crawl news websites')
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
        help='Target documents per language'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode (collect only 10 docs per site)'
    )

    args = parser.parse_args()

    # Load configurations
    config = load_config()
    sites_config = load_sites()

    # Determine target per site
    if args.test:
        target_per_site = 10
        print("\n[TEST MODE] Collecting only 10 documents per site\n")
    else:
        target_per_site = args.target // 5  # 5 sites per language

    # Determine languages
    if args.language == 'both':
        languages = ['bangla', 'english']
    else:
        languages = [args.language]

    # Crawl each language
    for language in languages:
        sites_key = f"{language}_sites"
        sites = sites_config[sites_key]

        # Crawl
        doc_store = crawl_language(language, sites, target_per_site, config)

        # Save documents
        output_dir = Path(__file__).parent.parent / 'data' / 'processed'
        output_file = output_dir / f"{language}_docs.json"

        doc_store.save(output_file)

        # Save metadata CSV
        metadata_file = output_dir / f"{language}_metadata.csv"
        doc_store.save_metadata_csv(metadata_file)

        # Print statistics
        stats = doc_store.get_statistics()
        print(f"\n{'='*60}")
        print(f"{language.upper()} CRAWL SUMMARY")
        print(f"{'='*60}")
        print(f"Total documents: {stats['total_documents']}")
        print(f"Average words: {stats['average_word_count']}")
        print(f"\nBy source:")
        for source, count in stats['by_source'].items():
            print(f"  {source}: {count}")
        print(f"{'='*60}\n")

    print("[DONE] Crawling complete!")


if __name__ == '__main__':
    main()
