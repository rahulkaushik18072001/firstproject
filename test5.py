from newsplease import NewsPlease
import requests
from bs4 import BeautifulSoup
import json
import datetime
from urllib.parse import urljoin

def find_rss_feeds(root_url):
    """Find all RSS feed URLs from the root URL"""
    print(f"Searching for RSS feeds at: {root_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    feeds = set()
    try:
        response = requests.get(root_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
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

def save_article_incrementally(article, filename):
    """Save a single article to JSON file incrementally"""
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(json.dumps(article, ensure_ascii=False) + ',')

def crawl_feed(feed_url, output_file):
    """Crawl articles from a single RSS feed and save incrementally"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(feed_url, headers=headers)
        soup = BeautifulSoup(response.text, 'xml')
        
        items = soup.find_all(['item', 'entry'])
        print(f"Found {len(items)} articles in feed: {feed_url}")
        
        for item in items:
            try:
                link = item.find(['link', 'guid'])
                if link:
                    article_url = link.get_text().strip()
                    print(f"Crawling: {article_url}")
                    
                    article = crawl_article(article_url)
                    
                    if article and article.maintext:
                        article_data = {
                            'title': article.title,
                            'text': article.maintext,
                            'url': article.url,
                            'authors': article.authors,
                            'date_publish': article.date_publish.isoformat() if article.date_publish else None,
                            'language': article.language,
                            'description': article.description,
                        }
                        save_article_incrementally(article_data, output_file)
                        print(f"Saved: {article.title}")
            except Exception as e:
                print(f"Error processing feed item: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Error crawling feed {feed_url}: {str(e)}")

def main():
    root_url = input("Enter the news website's RSS root URL (e.g., https://www.ndtv.com/rss): ")
    feeds = find_rss_feeds(root_url)
    
    if not feeds:
        print("No RSS feeds found!")
        return
        
    print(f"\nFound {len(feeds)} RSS feeds:")
    for feed in feeds:
        print(f"- {feed}")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"news_articles_{timestamp}.json"
    
    # Open file in write mode to clear previous content
    with open(output_file, 'w', encoding='utf-8') as f:
        pass
    
    for feed_url in feeds:
        print(f"\nProcessing feed: {feed_url}")
        crawl_feed(feed_url, output_file)
    
    print(f"\nCrawling completed. Articles saved to {output_file}")

if __name__ == "__main__":
    main()
