import feedparser
import newsplease
import json
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def fetch_rss_feed(url):
    """
    Fetches the RSS feed from the given URL and returns the parsed feed.
    """
    try:
        feed = feedparser.parse(url)
        if feed.bozo:
            raise Exception(f"Error parsing feed: {feed.bozo_exception}")
        return feed
    except Exception as e:
        logging.error(f"Failed to fetch RSS feed from {url}: {e}")
        sys.exit(1)

def extract_news_items(feed):
    """
    Extracts relevant information from each news item in the feed.
    """
    news_items = []
    for entry in feed.entries:
        try:
            article = newsplease.NewsPlease.from_url(entry.link)
            news_item = {
                'title': article.title,
                'link': article.url,
                'summary': article.maintext[:500],  # First 500 characters of the main text
                'published': article.date_publish,
                'author': article.authors,
                'image_url': article.image_url
            }
            news_items.append(news_item)
        except Exception as e:
            logging.warning(f"Failed to extract news item from {entry.link}: {e}")
    return news_items

def write_to_json(data, filename='news.json'):
    """
    Writes the extracted news data to a JSON file.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"News data successfully written to {filename}")
    except Exception as e:
        logging.error(f"Failed to write data to JSON file: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <rss_feed_url>")
        sys.exit(1)

    rss_feed_url = sys.argv[1]
    logging.info(f"Fetching RSS feed from {rss_feed_url}...")

    feed = fetch_rss_feed(rss_feed_url)
    news_items = extract_news_items(feed)
    
    logging.info(f"Extracted {len(news_items)} news items.")
    write_to_json(news_items)

if __name__ == "__main__":
    main()