from newsplease import NewsPlease
from newsplease.crawler.rss_crawler import RssCrawler
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import datetime
import json

def find_rss_feeds(root_url):
    """Find all RSS feed URLs from the root URL"""
    print(f"Searching for RSS feeds at: {root_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    feeds = set()
    try:
        # Get the root page
        response = requests.get(root_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find RSS links
        # Method 1: Look for link tags
        for link in soup.find_all('link', type=re.compile(r'(rss|xml|atom)')):
            href = link.get('href')
            if href:
                feeds.add(urljoin(root_url, href))
                
        # Method 2: Look for 'a' tags
        for link in soup.find_all('a', href=re.compile(r'(rss|xml|atom|feed)')):
            href = link.get('href')
            if href:
                feeds.add(urljoin(root_url, href))
        
        # Method 3: Common feed paths
        common_paths = [
            '/rss',
            '/feed',
            '/feeds',
            '/rss/feed',
            '/feed.xml',
            '/atom.xml',
            '/rss.xml'
        ]
        
        for path in common_paths:
            try:
                feed_url = urljoin(root_url, path)
                feed_response = requests.get(feed_url, headers=headers)
                if 'xml' in feed_response.headers.get('content-type', '').lower():
                    feeds.add(feed_url)
            except:
                continue
        
        return list(feeds)
        
    except Exception as e:
        print(f"Error finding RSS feeds: {str(e)}")
        return []

def crawl_feeds(feed_urls):
    """Crawl all discovered feeds"""
    crawler = RssCrawler()
    
    # Add all feeds to crawler
    for feed_url in feed_urls:
        print(f"Adding feed: {feed_url}")
        try:
            crawler.add_feed(feed_url)
        except Exception as e:
            print(f"Error adding feed {feed_url}: {str(e)}")
    
    # Crawl and collect articles
    articles = list(crawler.crawl())
    return articles

def save_articles(articles, filename):
    """Save articles to JSON file"""
    article_data = []
    
    for article in articles:
        data = {
            'title': article.title,
            'text': article.maintext,
            'url': article.url,
            'authors': article.authors,
            'date_publish': article.date_publish.isoformat() if article.date_publish else None,
            'language': article.language,
            'description': article.description,
        }
        article_data.append(data)
        
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(article_data, f, ensure_ascii=False, indent=2)

def main():
    # Get root URL from user
    root_url = input("Enter the news website's RSS root URL (e.g., https://www.ndtv.com/rss): ")
    
    # Find RSS feeds
    feeds = find_rss_feeds(root_url)
    
    if not feeds:
        print("No RSS feeds found!")
        return
        
    print(f"\nFound {len(feeds)} RSS feeds:")
    for feed in feeds:
        print(f"- {feed}")
    
    # Crawl articles from all feeds
    print("\nStarting to crawl feeds...")
    articles = crawl_feeds(feeds)
    
    if articles:
        # Save results
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"news_articles_{timestamp}.json"
        save_articles(articles, output_file)
        print(f"\nCompleted! Saved {len(articles)} articles to {output_file}")
    else:
        print("\nNo articles found.")

if __name__ == "__main__":
    main()