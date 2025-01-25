import requests
from bs4 import BeautifulSoup
import feedparser
from newsplease import NewsPlease
import datetime
import json
from datetime import timedelta
import re
from urllib.parse import urljoin, urlparse
import time

class RSSCrawler:
    def __init__(self, root_url, days_limit=2):
        self.root_url = root_url
        self.domain = urlparse(root_url).netloc
        self.days_limit = days_limit
        self.feed_urls = set()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def extract_article_content(self, url):
        """Extract article content using multiple methods"""
        try:
            # Method 1: Try using news-please
            article = NewsPlease.from_url(url)
            if article and article.text:
                return article.text
            
            # Method 2: Direct HTML parsing
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for elem in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                elem.decompose()
            
            # Try common article content selectors
            content = None
            selectors = [
                'article', 
                '.article-content',
                '.story-content',
                '[itemprop="articleBody"]',
                '.entry-content',
                '#content-body',
                '.story__content',
                '.article__body',
                '.article-text'
            ]
            
            for selector in selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(separator='\n', strip=True)
                    if len(content) > 100:  # Minimum content length check
                        break
            
            if not content:
                # Fallback: Try to find the largest text block
                paragraphs = soup.find_all('p')
                content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50)
            
            return content if content else None
            
        except Exception as e:
            print(f"Error extracting content from {url}: {str(e)}")
            return None

    def is_valid_feed(self, url):
        """Check if URL is a valid RSS/Atom feed"""
        try:
            feed = feedparser.parse(url)
            return bool(feed.entries) and hasattr(feed, 'version') and feed.version != ''
        except:
            return False

    def is_same_domain(self, url):
        """Check if URL belongs to same domain"""
        return urlparse(url).netloc == self.domain

    def get_all_rss_feeds(self):
        """Extract all RSS feed URLs from the root page"""
        try:
            response = requests.get(self.root_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            feed_patterns = [
                r'.*\.(rss|xml|atom)$',
                r'.*(rss|feed|atom|syndication).*'
            ]
            
            for link in soup.find_all(['a', 'link']):
                href = link.get('href', '')
                type_attr = link.get('type', '')
                
                if not href:
                    continue
                    
                absolute_url = urljoin(self.root_url, href)
                
                if not self.is_same_domain(absolute_url):
                    continue
                
                is_feed = False
                
                if any(feed_type in type_attr.lower() for feed_type in ['rss', 'atom', 'xml']):
                    is_feed = True
                    
                if any(re.match(pattern, href.lower()) for pattern in feed_patterns):
                    is_feed = True
                    
                if is_feed:
                    self.feed_urls.add(absolute_url)
            
            valid_feeds = set()
            for url in self.feed_urls:
                if self.is_valid_feed(url):
                    valid_feeds.add(url)
                    
            print(f"Found {len(valid_feeds)} valid RSS feeds")
            return valid_feeds
            
        except Exception as e:
            print(f"Error fetching RSS feeds: {str(e)}")
            return set()

    def is_within_days_limit(self, pub_date):
        if not pub_date:
            return False
        
        now = datetime.datetime.now(datetime.timezone.utc)
        limit_date = now - timedelta(days=self.days_limit)
        return pub_date >= limit_date

    def parse_date(self, date_str):
        try:
            date_formats = [
                '%a, %d %b %Y %H:%M:%S %z',
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%d %H:%M:%S',
                '%a, %d %b %Y %H:%M:%S %Z',
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.datetime.strptime(date_str, fmt)
                except:
                    continue
                    
            return None
        except:
            return None

    def crawl_feed(self, feed_url):
        """Crawl a single RSS feed"""
        articles = []
        
        print(f"\nProcessing feed: {feed_url}")
        feed = feedparser.parse(feed_url)
        
        if not feed.entries:
            print(f"No entries found in feed: {feed_url}")
            return []
        
        print(f"Found {len(feed.entries)} entries")
        
        for entry in feed.entries:
            try:
                pub_date = None
                for date_field in ['published', 'updated', 'pubDate']:
                    if hasattr(entry, date_field):
                        pub_date = self.parse_date(getattr(entry, date_field))
                        if pub_date:
                            break
                
                if not self.is_within_days_limit(pub_date):
                    continue
                
                # Extract article text
                print(f"Extracting content from: {entry.link}")
                article_text = self.extract_article_content(entry.link)
                
                # Add delay to avoid overwhelming the server
                time.sleep(1)
                
                if article_text:
                    article_data = {
                        'title': entry.get('title', ''),
                        'text': article_text,
                        'description': entry.get('description', ''),
                        'link': entry.link,
                        'published_date': pub_date.isoformat() if pub_date else None,
                        'authors': entry.get('authors', []),
                        'category': entry.get('category', ''),
                        'source_feed': feed_url,
                        'source_domain': self.domain
                    }
                    articles.append(article_data)
                    print(f"Successfully processed: {entry.get('title', '')}")
                else:
                    print(f"Could not extract content from: {entry.link}")
                    
            except Exception as e:
                print(f"Error processing article {entry.get('link', 'unknown')}: {str(e)}")
                continue
                
        return articles

    def crawl(self):
        """Main crawling method"""
        feed_urls = self.get_all_rss_feeds()
        if not feed_urls:
            print("No RSS feeds found!")
            return []
            
        all_articles = []
        for feed_url in feed_urls:
            articles = self.crawl_feed(feed_url)
            all_articles.extend(articles)
            
        return all_articles

def main():
    root_url = input("Enter the news website's RSS page URL: ")
    days_limit = int(input("Enter number of days to crawl (default 2): ") or 2)
    
    crawler = RSSCrawler(root_url, days_limit)
    
    print(f"\nCrawling articles from the last {days_limit} days...")
    articles = crawler.crawl()
    
    if articles:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = urlparse(root_url).netloc.replace('.', '_')
        output_file = "test.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
            
        print(f"\nCompleted! Saved {len(articles)} articles to {output_file}")
    else:
        print("\nNo articles found in the specified time period.")

if __name__ == "__main__":
    main()