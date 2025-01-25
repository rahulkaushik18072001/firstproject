import feedparser
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
from datetime import datetime
import logging
from typing import Dict, List, Optional
import concurrent.futures
from pathlib import Path

class RSSCrawler:
    def __init__(
        self,
        root_url: str,
        output_file: str = "articles.json",
        max_articles: int = 100,
        rate_limit: float = 1.0
    ):
        """
        Initialize the RSS crawler.
        
        Args:
            root_url: Root URL of the website to crawl
            output_file: Path to save the JSON output
            max_articles: Maximum number of articles to crawl
            rate_limit: Minimum time between requests in seconds
        """
        self.root_url = root_url.rstrip('/')
        self.output_file = output_file
        self.max_articles = max_articles
        self.rate_limit = rate_limit
        self.last_request_time = 0
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def discover_feeds(self) -> List[str]:
        """Find RSS feed URLs from the root URL."""
        try:
            self._respect_rate_limit()
            response = requests.get(self.root_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for RSS/Atom feed links
            feed_urls = []
            feed_links = soup.find_all('link', type=lambda t: t and ('rss' in t or 'atom' in t))
            
            for link in feed_links:
                feed_url = link.get('href', '')
                if feed_url:
                    feed_url = urljoin(self.root_url, feed_url)
                    feed_urls.append(feed_url)
            
            # Common RSS paths to try if none found
            common_paths = [
                '/feed',
                '/rss',
                '/feed/rss',
                '/rss.xml',
                '/atom.xml',
                '/feed.xml'
            ]
            
            for path in common_paths:
                if not feed_urls:
                    test_url = urljoin(self.root_url, path)
                    try:
                        self._respect_rate_limit()
                        response = requests.get(test_url, timeout=5)
                        if response.status_code == 200 and ('xml' in response.headers.get('content-type', '')):
                            feed_urls.append(test_url)
                    except requests.RequestException:
                        continue
            
            return feed_urls
        
        except requests.RequestException as e:
            self.logger.error(f"Error discovering feeds: {str(e)}")
            return []

    def _respect_rate_limit(self):
        """Ensure we don't exceed the rate limit."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last_request)
        self.last_request_time = time.time()

    def extract_article_content(self, url: str) -> Dict:
        """Extract article content from a URL."""
        try:
            self._respect_rate_limit()
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find article content (customize based on site structure)
            content = ""
            article_tag = soup.find('article') or soup.find('div', class_=['article', 'post', 'content'])
            if article_tag:
                # Remove unwanted elements
                for unwanted in article_tag.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    unwanted.decompose()
                content = article_tag.get_text(strip=True)
            
            return {
                'full_text': content,
                'word_count': len(content.split()),
                'extracted_at': datetime.now().isoformat()
            }
        except requests.RequestException as e:
            self.logger.error(f"Error extracting content from {url}: {str(e)}")
            return {}

    def process_feed(self, feed_url: str) -> List[Dict]:
        """Process a single RSS feed and extract articles."""
        try:
            feed = feedparser.parse(feed_url)
            articles = []
            
            for entry in feed.entries[:self.max_articles]:
                article = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'author': entry.get('author', ''),
                    'summary': entry.get('summary', ''),
                    'categories': entry.get('tags', []),
                }
                
                # Extract full content if available
                if hasattr(entry, 'content'):
                    article['content'] = entry.content[0].value
                else:
                    # Fetch and extract content from the article URL
                    article.update(self.extract_article_content(article['link']))
                
                articles.append(article)
            
            return articles
        
        except Exception as e:
            self.logger.error(f"Error processing feed {feed_url}: {str(e)}")
            return []

    def crawl(self):
        """Main crawling function."""
        try:
            # Discover RSS feeds
            feed_urls = self.discover_feeds()
            if not feed_urls:
                raise ValueError("No RSS feeds found")
            
            self.logger.info(f"Found {len(feed_urls)} RSS feeds")
            
            # Process feeds in parallel
            all_articles = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_to_url = {executor.submit(self.process_feed, url): url for url in feed_urls}
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        articles = future.result()
                        all_articles.extend(articles)
                        self.logger.info(f"Processed {len(articles)} articles from {url}")
                    except Exception as e:
                        self.logger.error(f"Error processing {url}: {str(e)}")
            
            # Save results
            output_path = Path(self.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_articles, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Saved {len(all_articles)} articles to {self.output_file}")
            return all_articles
        
        except Exception as e:
            self.logger.error(f"Crawling failed: {str(e)}")
            return []

def main():
    # Example usage
    crawler = RSSCrawler(
        root_url="https://ndtv.com",
        output_file="articleslafda.json",
        max_articles=100,
        rate_limit=1.0
    )
    crawler.crawl()

if __name__ == "__main__":
    main()