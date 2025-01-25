import requests
from bs4 import BeautifulSoup
import feedparser
from newsplease import NewsPlease
import datetime
import json
from datetime import timedelta
import re
from pathlib import Path

def get_all_rss_feeds(root_url):
    """
    Extract all RSS feed URLs from NDTV's RSS page
    """
    try:
        response = requests.get(root_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links that end with "rss" or contain "feeds"
        feed_urls = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('rss') or 'feeds' in href.lower():
                if not href.startswith('http'):
                    href = 'https://www.ndtv.com' + href
                feed_urls.append(href)
                
        print(f"Found {len(feed_urls)} RSS feeds")
        return feed_urls
    except Exception as e:
        print(f"Error fetching RSS feeds: {str(e)}")
        return []

def is_within_last_two_days(pub_date):
    """Check if article is within last 2 days"""
    if not pub_date:
        return False
    
    now = datetime.datetime.now(datetime.timezone.utc)
    two_days_ago = now - timedelta(days=2)
    return pub_date >= two_days_ago

def parse_date(date_str):
    """Parse date string to datetime object"""
    try:
        return datetime.datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
    except:
        return None

def append_to_json(article_data, output_file):
    """Append a single article to the JSON file"""
    try:
        # Read existing data
        if Path(output_file).exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                try:
                    articles = json.load(f)
                except json.JSONDecodeError:
                    articles = []
        else:
            articles = []
        
        # Append new article
        articles.append(article_data)
        
        # Write back to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
            
        print(f"Appended article to {output_file}")
    except Exception as e:
        print(f"Error appending to JSON: {str(e)}")

def crawl_feed(feed_url, output_file):
    """Crawl a single RSS feed"""
    print(f"\nProcessing feed: {feed_url}")
    feed = feedparser.parse(feed_url)
    
    if not feed.entries:
        print(f"No entries found in feed: {feed_url}")
        return 0
    
    print(f"Found {len(feed.entries)} entries")
    processed_count = 0
    
    for entry in feed.entries:
        try:
            # Get publication date
            pub_date = None
            if hasattr(entry, 'published'):
                pub_date = parse_date(entry.published)
            
            # Skip if article is older than 2 days
            if not is_within_last_two_days(pub_date):
                continue
            
            # Extract article content
            article = NewsPlease.from_url(entry.link)
            
            if article:
                article_data = {
                    'title': article.title,
                    'text': article.text,
                    'description': entry.get('description', ''),
                    'link': entry.link,
                    'published_date': pub_date.isoformat() if pub_date else None,
                    'authors': article.authors,
                    'category': entry.get('category', ''),
                    'source_feed': feed_url
                }
                
                # Append article immediately
                append_to_json(article_data, output_file)
                processed_count += 1
                print(f"Processed: {article.title}")
                
        except Exception as e:
            print(f"Error processing article {entry.get('link', 'unknown')}: {str(e)}")
            continue
            
    return processed_count

def main():
    root_url = "https://www.ndtv.com/rss"
    
    # Create output filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"ndtv_articles_{timestamp}.json"
    
    # Create empty JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump([], f)
    
    # Get all RSS feed URLs
    feed_urls = get_all_rss_feeds(root_url)
    if not feed_urls:
        print("No RSS feeds found!")
        return
        
    # Process all feeds
    total_articles = 0
    for feed_url in feed_urls:
        articles_processed = crawl_feed(feed_url, output_file)
        total_articles += articles_processed
    
    print(f"\nCompleted! Processed {total_articles} articles from the last 2 days")
    print(f"Final output file: {output_file}")

if __name__ == "__main__":
    main()