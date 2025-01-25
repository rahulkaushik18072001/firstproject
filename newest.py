import requests
from bs4 import BeautifulSoup
import feedparser
from newsplease import NewsPlease
import datetime
import json
from datetime import timedelta
import re
from pathlib import Path
import html

def extract_article_text(entry):
    """
    Extract article text using multiple methods, prioritizing RSS content
    """
    try:
        # Method 1: Try to get content from RSS feed's content:encoded field
        if hasattr(entry, 'content') and entry.content:
            # Some feeds store content in entry.content[0].value
            return BeautifulSoup(entry.content[0].value, 'html.parser').get_text(separator=' ', strip=True)
            
        # Method 2: Try to get content from content_encoded field
        if hasattr(entry, 'content_encoded') and entry.content_encoded:
            return BeautifulSoup(entry.content_encoded, 'html.parser').get_text(separator=' ', strip=True)
            
        # Method 3: Try website scraping as fallback
        article = NewsPlease.from_url(entry.link)
        if article and article.text:
            return article.text
            
        # Method 4: Direct requests + BeautifulSoup as final fallback
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(entry.link, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try common article content selectors
        content_selectors = [
            'div.article',
            'div[id*="content-body"]',
            'div.article-text',
            'div[itemprop="articleBody"]',
            'div.story-content',  # NDTV specific
            'div.content_text'    # NDTV specific
        ]
        
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                # Remove unwanted elements
                for unwanted in content.select('script, style, iframe, div.ad-container'):
                    unwanted.decompose()
                    
                text = content.get_text(separator=' ', strip=True)
                if text:
                    return text
                    
        # If still no text, try getting all paragraphs
        paragraphs = soup.find_all('p')
        if paragraphs:
            text = ' '.join(p.get_text().strip() for p in paragraphs)
            text = re.sub(r'\s+', ' ', text).strip()
            return text if text else None
            
    except Exception as e:
        print(f"Error extracting text from article: {str(e)}")
    
    return None

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
            
            # Extract article text using our enhanced method
            article_text = extract_article_text(entry)
            
            article_data = {
                'title': entry.title,
                'text': article_text,
                'description': entry.get('description', ''),
                'link': entry.link,
                'published_date': pub_date.isoformat() if pub_date else None,
                'authors': entry.get('authors', []) if hasattr(entry, 'authors') else [],
                'category': entry.get('category', ''),
                'source_feed': feed_url
            }
            
            # Append article immediately
            append_to_json(article_data, output_file)
            processed_count += 1
            print(f"Processed: {entry.title}")
            print(f"Text extracted: {bool(article_text)}")  # Debug info
            
        except Exception as e:
            print(f"Error processing article {entry.get('link', 'unknown')}: {str(e)}")
            continue
            
    return processed_count

# ... (rest of the code remains the same) ...

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