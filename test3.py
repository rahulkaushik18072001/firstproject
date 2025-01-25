from newsplease import NewsPlease
import requests
from bs4 import BeautifulSoup
import json
import datetime
from urllib.parse import urljoin
import re

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
        for link in soup.find_all(['link', 'a'], href=True):
            href = link.get('href', '')
            if 'rss' in href.lower() or 'feed' in href.lower() or 'atom' in href.lower():
                full_url = urljoin(root_url, href)
                feeds.add(full_url)
                
        return list(feeds)
        
    except Exception as e:
        print(f"Error finding RSS feeds: {str(e)}")
        return []

def crawl_article(url):
    """Crawl a single article using NewsPlease"""
    try:
        article = NewsPlease.from_url(url)
        return article
    except Exception as e:
        print(f"Error crawling article {url}: {str(e)}")
        return None

def crawl_feed(feed_url):
    """Crawl articles from a single RSS feed"""
    try:
        # Parse the RSS feed
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(feed_url, headers=headers)
        soup = BeautifulSoup(response.text, 'xml')
        
        articles = []
        
        # Find all items/entries in the feed
        items = soup.find_all(['item', 'entry'])
        
        print(f"Found {len(items)} articles in feed: {feed_url}")
        
        for item in items:
            try:
                # Get article link
                link = item.find(['link', 'guid'])
                if link:
                    article_url = link.get_text().strip()
                    print(f"Crawling: {article_url}")
                    
                    # Crawl article
                    article = crawl_article(article_url)
                    
                    if article and article.maintext:
                        articles.append({
                            'title': article.title,
                            'text': article.maintext,
                            'url': article.url,
                            'authors': article.authors,
                            'date_publish': article.date_publish.isoformat() if article.date_publish else None,
                            'language': article.language,
                            'description': article.description,
                        })
                        print(f"Successfully crawled: {article.title}")
            except Exception as e:
                print(f"Error processing feed item: {str(e)}")
                continue
                
        return articles
        
    except Exception as e:
        print(f"Error crawling feed {feed_url}: {str(e)}")
        return []

def save_articles(articles, filename):
    """Save articles to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

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
    all_articles = []
    for feed_url in feeds:
        print(f"\nProcessing feed: {feed_url}")
        articles = crawl_feed(feed_url)
        all_articles.extend(articles)
    
    if all_articles:
        # Save results
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"news_articles_{timestamp}.json"
        save_articles(all_articles, output_file)
        print(f"\nCompleted! Saved {len(all_articles)} articles to {output_file}")
    else:
        print("\nNo articles found.")

if __name__ == "__main__":
    main()