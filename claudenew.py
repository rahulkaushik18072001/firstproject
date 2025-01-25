import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import logging
from dateutil import parser
from urllib.parse import urljoin
import time
import os
from datetime import timezone

class RSSCrawler:
    def __init__(self, root_url):
        """Initialize the RSS crawler with a root URL."""
        self.root_url = root_url
        self.setup_logging()
        
    def setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('rss_crawler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def discover_feeds(self):
        """Discover RSS feeds from the root URL."""
        try:
            response = requests.get(self.root_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            feed_urls = set()
            
            for link in soup.find_all('link'):
                if link.get('type') in ['application/rss+xml', 'application/atom+xml']:
                    feed_urls.add(urljoin(self.root_url, link.get('href')))
            
            for a in soup.find_all('a'):
                href = a.get('href', '')
                if any(x in href.lower() for x in ['/rss', '/feed', '.xml', 'atom']):
                    feed_urls.add(urljoin(self.root_url, href))
            
            return list(feed_urls)
        except Exception as e:
            self.logger.error(f"Error discovering feeds from {self.root_url}: {str(e)}")
            return []

    def parse_date(self, date_str):
        """Parse date string to timezone-aware datetime object."""
        try:
            # Parse the date string
            dt = parser.parse(date_str)
            
            # If the datetime is naive (has no timezone info), assume UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
                
            return dt
        except Exception as e:
            self.logger.error(f"Error parsing date {date_str}: {str(e)}")
            return None

    def extract_main_content(self, url):
        """Extract main content from article URL."""
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            content = None
            
            if soup.find('article'):
                content = soup.find('article')
            elif soup.find('main'):
                content = soup.find('main')
            elif soup.find('div', class_=['content', 'article-content', 'post-content', 'entry-content']):
                content = soup.find('div', class_=['content', 'article-content', 'post-content', 'entry-content'])
            
            if content:
                return ' '.join(content.stripped_strings)
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting content from {url}: {str(e)}")
            return None

    def extract_image(self, entry, article_soup):
        """Extract image URL from feed entry or article content."""
        try:
            if 'media_content' in entry:
                return entry.media_content[0]['url']
            elif 'media_thumbnail' in entry:
                return entry.media_thumbnail[0]['url']
            
            if article_soup:
                img = article_soup.find('img', class_=['featured-image', 'article-image'])
                if img and img.get('src'):
                    return img['src']
                
                meta_img = article_soup.find('meta', property='og:image')
                if meta_img:
                    return meta_img['content']
                
            return None
        except Exception as e:
            self.logger.error(f"Error extracting image: {str(e)}")
            return None

    def crawl_feed(self, feed_url):
        """Crawl a single RSS feed."""
        articles = []
        try:
            feed = feedparser.parse(feed_url)
            # Make cutoff date timezone-aware
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=2)
            
            for entry in feed.entries:
                try:
                    # Parse publication date
                    pub_date = self.parse_date(entry.get('published', entry.get('updated', '')))
                    if not pub_date or pub_date < cutoff_date:
                        continue
                    
                    article_url = entry.link
                    article_content = self.extract_main_content(article_url)
                    
                    if article_content:
                        article = {
                            'title': entry.get('title', ''),
                            'author': entry.get('author', ''),
                            'description': entry.get('description', ''),
                            'text': article_content,
                            'link': article_url,
                            'published_date': pub_date.isoformat(),
                            'image_link': self.extract_image(entry, BeautifulSoup(article_content, 'html.parser'))
                        }
                        articles.append(article)
                    
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Error processing entry from {feed_url}: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error crawling feed {feed_url}: {str(e)}")
            
        return articles

    def save_articles(self, articles, output_file='articles.json'):
        """Save articles to JSON file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Saved {len(articles)} articles to {output_file}")
        except Exception as e:
            self.logger.error(f"Error saving articles to file: {str(e)}")

    def run(self, output_file='articlesthehindubitch.json'):
        """Run the crawler."""
        all_articles = []
        
        feed_urls = self.discover_feeds()
        self.logger.info(f"Discovered {len(feed_urls)} feeds")
        
        for feed_url in feed_urls:
            self.logger.info(f"Crawling feed: {feed_url}")
            articles = self.crawl_feed(feed_url)
            all_articles.extend(articles)
            
        self.save_articles(all_articles, output_file)
        return all_articles

def main():
    root_url = "https://www.thehindu.com/rssfeeds/"  # Example URL
    crawler = RSSCrawler(root_url)
    crawler.run()

if __name__ == "__main__":
    main()